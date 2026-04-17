#!/usr/bin/env python3
"""Claude Code session board: ranked, filterable picker to resume past sessions.

Keys:
  ↑/↓ or j/k   move
  l            sort by line count (default)
  d            sort by date (mtime)
  /            filter by title/project substring (ESC to clear)
  Enter        resume selected session
  q            quit
"""
import curses
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
TITLES_CACHE = Path.home() / ".claude" / "scripts" / "titles.json"
GEN_TITLE_SCRIPT = Path.home() / ".claude" / "scripts" / "gen_title.py"
MIN_LINES = 10


def load_titles_cache():
    if TITLES_CACHE.exists():
        try:
            return json.loads(TITLES_CACHE.read_text())
        except Exception:
            pass
    return {}


def spawn_background_reindex():
    try:
        subprocess.Popen(
            ["python3", str(GEN_TITLE_SCRIPT), "--reindex"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception:
        pass


def session_has_compaction(jsonl_path: Path) -> bool:
    try:
        with jsonl_path.open("r", errors="replace") as fh:
            for line in fh:
                if '"compact_boundary"' in line or '"isCompactSummary":true' in line:
                    return True
    except Exception:
        pass
    return False


def extract_cwd(jsonl_path: Path, max_scan: int = 60):
    try:
        with jsonl_path.open("r", errors="replace") as fh:
            for i, line in enumerate(fh):
                if i >= max_scan:
                    break
                if '"cwd"' not in line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                cwd = obj.get("cwd")
                if isinstance(cwd, str) and cwd:
                    return cwd
    except Exception:
        pass
    return None


def shorten(p: str) -> str:
    if not p:
        return "?"
    home = str(Path.home())
    if p.startswith(home):
        return "~" + p[len(home):]
    return p


def extract_title(path: Path, max_scan: int = 40) -> str:
    try:
        with path.open("r", errors="replace") as f:
            for i, line in enumerate(f):
                if i >= max_scan:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get("type") != "user":
                    continue
                msg = obj.get("message", {})
                content = msg.get("content", "")
                text = ""
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    for b in content:
                        if isinstance(b, dict) and b.get("type") == "text":
                            text = b.get("text", "")
                            break
                        if isinstance(b, dict) and "content" in b:
                            continue
                text = text.strip()
                if not text or text.startswith("<"):
                    continue
                if "tool_use_id" in str(obj):
                    continue
                text = " ".join(text.split())
                return text[:80]
    except Exception:
        pass
    return "(no title)"


def scan_sessions():
    rows = []
    if not PROJECTS.exists():
        return rows
    titles = load_titles_cache()
    for proj_dir in PROJECTS.iterdir():
        if not proj_dir.is_dir():
            continue
        for f in proj_dir.glob("*.jsonl"):
            try:
                with f.open("rb") as fh:
                    lines = sum(1 for _ in fh)
            except Exception:
                continue
            if lines < MIN_LINES:
                continue
            mtime = f.stat().st_mtime
            sid = f.stem
            entry = titles.get(sid) or {}
            cached_title = entry.get("title")
            cached_fresh = cached_title and entry.get("source_mtime") == mtime
            title = cached_title if cached_title else extract_title(f)
            cwd = extract_cwd(f) or str(Path.home())
            compacted = session_has_compaction(f)
            rows.append({
                "lines": lines,
                "mtime": mtime,
                "date": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d"),
                "project_dir": proj_dir.name,
                "cwd": cwd,
                "project": shorten(cwd),
                "session_id": sid,
                "short_id": sid[:8],
                "title": title,
                "title_fresh": bool(cached_fresh),
                "compacted": compacted,
                "path": str(f),
            })
    return rows


def draw(stdscr, rows, sort_mode, filter_str, sel):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    body_attr = curses.color_pair(1)
    bar_attr = curses.color_pair(2) | curses.A_BOLD
    header_attr = curses.color_pair(1) | curses.A_BOLD
    sel_attr = curses.color_pair(3) | curses.A_BOLD

    if sort_mode == "l":
        rows_sorted = sorted(rows, key=lambda r: -r["lines"])
    else:
        rows_sorted = sorted(rows, key=lambda r: -r["mtime"])
    if filter_str:
        fl = filter_str.lower()
        rows_sorted = [r for r in rows_sorted if fl in r["title"].lower() or fl in r["project"].lower()]
    sel = max(0, min(sel, len(rows_sorted) - 1)) if rows_sorted else 0

    header = f" Claude Session Board  [{len(rows_sorted)}/{len(rows)}]  sort=[{'lines' if sort_mode=='l' else 'date'}]  filter='{filter_str}' "
    stdscr.addnstr(0, 0, header.ljust(w - 1), w - 1, bar_attr)
    col = " #   LINES C DATE        PROJECT                           TITLE"
    stdscr.addnstr(1, 0, col.ljust(w - 1), w - 1, header_attr)

    body_h = h - 4
    top = max(0, sel - body_h // 2)
    top = min(top, max(0, len(rows_sorted) - body_h))
    for i in range(body_h):
        idx = top + i
        if idx >= len(rows_sorted):
            break
        r = rows_sorted[idx]
        mark = " " if r.get("title_fresh") else "~"
        compact_flag = "C" if r.get("compacted") else " "
        line = f" {idx+1:<3} {r['lines']:>5} {compact_flag} {r['date']}  {r['project'][:33]:<33} {mark}{r['title']}"
        attr = sel_attr if idx == sel else body_attr
        stdscr.addnstr(2 + i, 0, line.ljust(w - 1), w - 1, attr)

    foot = " [Enter] resume  [v]iew raw  [l]ines  [d]ate  [/] filter  [q]uit   ~=title pending "
    stdscr.addnstr(h - 1, 0, foot.ljust(w - 1), w - 1, bar_attr)
    stdscr.refresh()
    return rows_sorted, sel


def prompt_filter(stdscr, current):
    h, w = stdscr.getmaxyx()
    curses.echo()
    stdscr.addnstr(h - 1, 0, " filter: ".ljust(w - 1), w - 1, curses.A_REVERSE)
    stdscr.move(h - 1, 9)
    try:
        s = stdscr.getstr(h - 1, 9, min(60, w - 10)).decode("utf-8", "ignore")
    except Exception:
        s = current
    curses.noecho()
    return s


def view_transcript(stdscr, row):
    chunks = []
    try:
        with open(row["path"], "r", errors="replace") as fh:
            for line in fh:
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                t = o.get("type")
                if t not in ("user", "assistant"):
                    continue
                m = o.get("message", {}) or {}
                c = m.get("content", "")
                text = ""
                if isinstance(c, str):
                    text = c
                elif isinstance(c, list):
                    for b in c:
                        if isinstance(b, dict) and b.get("type") == "text":
                            text += b.get("text", "")
                text = text.strip()
                if not text or text.startswith("<system-reminder") or text.startswith("<command-"):
                    continue
                ts = o.get("timestamp", "")
                role = "USER" if t == "user" else "ASSISTANT"
                chunks.append(f"\n===== {role}  {ts} =====\n\n{text}\n")
    except Exception as e:
        chunks = [f"(failed to read: {e})"]
    body = "".join(chunks) if chunks else "(no text messages in this session)"
    header = (
        f"Session {row['short_id']}  |  {row['lines']} lines  |  {row['date']}  |  "
        f"{row['project']}\nTitle: {row['title']}\nPath:  {row['path']}\n"
        f"{'=' * 72}\n"
    )
    curses.def_prog_mode()
    curses.endwin()
    try:
        proc = subprocess.Popen(["less", "-R"], stdin=subprocess.PIPE)
        proc.communicate((header + body).encode("utf-8", "replace"))
    except FileNotFoundError:
        print(header + body)
        input("\n(press Enter to return)")
    curses.reset_prog_mode()
    stdscr.refresh()


def ui(stdscr, rows):
    curses.curs_set(0)
    stdscr.keypad(True)
    curses.start_color()
    try:
        curses.use_default_colors()
    except curses.error:
        pass
    # Paper-and-ink theme: warm cream background, dark ink text, highlight yellow for selection.
    PAPER = 16   # warm cream
    INK = 17     # dark brown-black ink
    HIGHLIGHT = 18  # selection — richer yellow
    BAR = 19     # muted ochre bar
    use_custom = curses.can_change_color() and curses.COLORS >= 20
    if use_custom:
        try:
            curses.init_color(PAPER, 988, 965, 890)      # #FCF6E3 ivory
            curses.init_color(INK, 160, 130, 95)          # #29211A dark ink
            curses.init_color(HIGHLIGHT, 960, 870, 450)   # #F5DE73 marker yellow
            curses.init_color(BAR, 890, 820, 620)         # #E3D19E parchment band
        except curses.error:
            use_custom = False
    if use_custom:
        curses.init_pair(1, INK, PAPER)
        curses.init_pair(2, INK, BAR)
        curses.init_pair(3, INK, HIGHLIGHT)
    else:
        # Fallback for terminals that don't allow init_color.
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_YELLOW)
    stdscr.bkgd(" ", curses.color_pair(1))
    sort_mode = "l"
    filter_str = ""
    sel = 0
    while True:
        visible, sel = draw(stdscr, rows, sort_mode, filter_str, sel)
        ch = stdscr.getch()
        if ch in (ord("q"), 27):
            return None
        elif ch in (curses.KEY_DOWN, ord("j")):
            sel = min(sel + 1, max(0, len(visible) - 1))
        elif ch in (curses.KEY_UP, ord("k")):
            sel = max(sel - 1, 0)
        elif ch == curses.KEY_NPAGE:
            sel = min(sel + 10, max(0, len(visible) - 1))
        elif ch == curses.KEY_PPAGE:
            sel = max(sel - 10, 0)
        elif ch == ord("l"):
            sort_mode = "l"; sel = 0
        elif ch == ord("d"):
            sort_mode = "d"; sel = 0
        elif ch == ord("/"):
            filter_str = prompt_filter(stdscr, filter_str)
            sel = 0
        elif ch == ord("v"):
            if visible:
                view_transcript(stdscr, visible[sel])
        elif ch in (curses.KEY_ENTER, 10, 13):
            if visible:
                row = visible[sel]
                if row.get("compacted"):
                    h, w = stdscr.getmaxyx()
                    msg = " This session was compacted — resume will start from the summary.  [v]iew raw  [r]esume anyway  [c]ancel "
                    stdscr.addnstr(h - 1, 0, msg.ljust(w - 1), w - 1, curses.color_pair(3) | curses.A_BOLD)
                    stdscr.refresh()
                    while True:
                        k = stdscr.getch()
                        if k in (ord("c"), 27):
                            break
                        if k == ord("v"):
                            view_transcript(stdscr, row)
                            break
                        if k == ord("r") or k in (curses.KEY_ENTER, 10, 13):
                            return row
                else:
                    return row


def main():
    rows = scan_sessions()
    if not rows:
        print("No sessions found in", PROJECTS)
        sys.exit(1)
    spawn_background_reindex()
    choice = curses.wrapper(ui, rows)
    if not choice:
        sys.exit(0)

    cwd = choice.get("cwd") or os.path.expanduser("~")
    if not os.path.isdir(cwd):
        cwd = os.path.expanduser("~")
    os.chdir(cwd)
    print(f"Resuming {choice['short_id']} in {cwd} ...")
    try:
        os.execvp("claude", ["claude", "--resume", choice["session_id"]])
    except FileNotFoundError:
        print("`claude` CLI not found on PATH.")
        sys.exit(1)


if __name__ == "__main__":
    main()
