#!/usr/bin/env python3
"""Generate concise titles for Claude Code sessions via `claude -p`.

Usage:
  gen_title.py <session_id>       # regenerate one
  gen_title.py --reindex          # regenerate all stale/missing
  gen_title.py                    # hook mode: reads {session_id} JSON on stdin

Cache: ~/.claude/scripts/titles.json
  { "<session_id>": {"title": str, "source_mtime": float, "generated_at": float} }
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
CACHE_PATH = Path.home() / ".claude" / "scripts" / "titles.json"
LOCK_PATH = Path.home() / ".claude" / "scripts" / ".titles.lock"
MODEL = "claude-haiku-4-5-20251001"
MIN_LINES = 10
THROTTLE_SECONDS = 300
MAX_CONTENT_CHARS = 4000
CALL_TIMEOUT = 90


def load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text())
        except Exception:
            pass
    return {}


def save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cache, indent=2, sort_keys=True))
    tmp.replace(CACHE_PATH)


def find_jsonl(session_id: str):
    if not PROJECTS.exists():
        return None
    for d in PROJECTS.iterdir():
        if not d.is_dir():
            continue
        f = d / f"{session_id}.jsonl"
        if f.exists():
            return f
    return None


def extract_content(jsonl_path: Path, max_chars: int = MAX_CONTENT_CHARS) -> str:
    parts = []
    total = 0
    try:
        with jsonl_path.open("r", errors="replace") as fh:
            for line in fh:
                if total >= max_chars:
                    break
                if '"tool_use_id"' in line or '"tool_result"' in line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                t = obj.get("type")
                if t not in ("user", "assistant"):
                    continue
                msg = obj.get("message", {}) or {}
                content = msg.get("content", "")
                text = ""
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    for b in content:
                        if isinstance(b, dict) and b.get("type") == "text":
                            text += b.get("text", "")
                text = " ".join(text.split()).strip()
                if not text:
                    continue
                if text.startswith("<system-reminder") or text.startswith("<command-"):
                    continue
                prefix = "User: " if t == "user" else "Assistant: "
                snippet = prefix + text[:500]
                parts.append(snippet)
                total += len(snippet)
    except Exception:
        return ""
    return "\n".join(parts)[:max_chars]


def call_claude(prompt: str):
    try:
        res = subprocess.run(
            ["claude", "-p", prompt, "--model", MODEL],
            capture_output=True,
            text=True,
            timeout=CALL_TIMEOUT,
        )
    except Exception:
        return None
    if res.returncode != 0:
        return None
    out = (res.stdout or "").strip()
    if not out:
        return None
    for raw in out.split("\n"):
        line = raw.strip()
        if not line:
            continue
        # skip markdown headers, bullets, preambles
        while line and line[0] in "#*->`":
            line = line[1:].lstrip()
        if line.lower().startswith(("title:", "session:", "topic:")):
            line = line.split(":", 1)[1].strip()
        line = line.strip('"\'').rstrip(".!?,:;")
        line = " ".join(line.split())
        if len(line) < 3:
            continue
        return line[:70]
    return None


def generate_one(session_id: str, jsonl_path: Path, cache: dict, force: bool = False) -> bool:
    src_mtime = jsonl_path.stat().st_mtime
    entry = cache.get(session_id) or {}
    if not force:
        if entry.get("title") and entry.get("source_mtime") == src_mtime:
            return False
        if entry.get("title") and (time.time() - entry.get("generated_at", 0) < THROTTLE_SECONDS):
            return False
    content = extract_content(jsonl_path)
    if not content:
        return False
    prompt = (
        "Task: Read the transcript below (delimited by <<<>>>) and respond with a single English title.\n"
        "Rules for your response:\n"
        "- 5 to 8 words\n"
        "- English only, even if the transcript is in another language\n"
        "- Describe the main task or topic of the session\n"
        "- Plain text only: no quotes, no markdown, no '#', no '-', no 'Title:' prefix, no trailing punctuation\n"
        "- Respond with the title and nothing else. Do not add any explanation or commentary.\n\n"
        "<<<\n" + content + "\n>>>\n\nTitle:"
    )
    title = call_claude(prompt)
    if not title:
        return False
    cache[session_id] = {
        "title": title,
        "source_mtime": src_mtime,
        "generated_at": time.time(),
    }
    return True


def acquire_lock():
    try:
        fd = os.open(str(LOCK_PATH), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        try:
            pid = int(LOCK_PATH.read_text().strip() or "0")
            os.kill(pid, 0)
            return False
        except (OSError, ValueError):
            LOCK_PATH.unlink(missing_ok=True)
            return acquire_lock()


def release_lock():
    LOCK_PATH.unlink(missing_ok=True)


def reindex_all():
    if not acquire_lock():
        return
    try:
        cache = load_cache()
        targets = []
        for d in PROJECTS.iterdir():
            if not d.is_dir():
                continue
            for f in d.glob("*.jsonl"):
                try:
                    with f.open("rb") as fh:
                        lines = sum(1 for _ in fh)
                except Exception:
                    continue
                if lines < MIN_LINES:
                    continue
                sid = f.stem
                entry = cache.get(sid) or {}
                if entry.get("title") and entry.get("source_mtime") == f.stat().st_mtime:
                    continue
                targets.append((sid, f, lines))
        targets.sort(key=lambda x: -x[2])
        for sid, path, _ in targets:
            if generate_one(sid, path, cache):
                save_cache(cache)
    finally:
        release_lock()


def hook_mode():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    sid = data.get("session_id")
    if not sid:
        return
    jsonl = find_jsonl(sid)
    if not jsonl:
        return
    cache = load_cache()
    if generate_one(sid, jsonl, cache):
        save_cache(cache)


def main():
    args = sys.argv[1:]
    if not args:
        if not sys.stdin.isatty():
            hook_mode()
        return
    if args[0] == "--reindex":
        reindex_all()
        return
    sid = args[0]
    force = "--force" in args
    jsonl = find_jsonl(sid)
    if not jsonl:
        print(f"no jsonl for {sid}", file=sys.stderr)
        sys.exit(1)
    cache = load_cache()
    if generate_one(sid, jsonl, cache, force=force):
        save_cache(cache)
        print(cache[sid]["title"])
    else:
        print(cache.get(sid, {}).get("title", "(unchanged)"))


if __name__ == "__main__":
    main()
