#!/usr/bin/env python3
"""study — 10× learning tool for Abby.

Builds interactive per-class study sites from course material with:
  · Chinese 中文总结 for every concept
  · Visual diagrams (Mermaid, KaTeX, SVG)
  · Active-recall questions + worked examples
  · Voice-input chat box wired to openclaw (MiniMax-M2.5, local)

Folders: ~/Desktop/coursework/<class>/{raw,site}/

Commands:
  study                        list classes
  study init <class>           scaffold folders + template
  study serve <class>          start local server + openclaw chat proxy
  study open <class>           serve and open in browser (alias)
"""
import http.server
import json
import os
import shutil
import socketserver
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path.home() / "Desktop" / "coursework"
TEMPLATE = Path.home() / ".local" / "share" / "study" / "template.html"
PORT = 8765


def path_for(cls: str) -> Path:
    return ROOT / cls


def cmd_init(cls: str):
    p = path_for(cls)
    (p / "raw").mkdir(parents=True, exist_ok=True)
    (p / "site").mkdir(parents=True, exist_ok=True)
    idx = p / "site" / "index.html"
    if not idx.exists():
        if TEMPLATE.exists():
            html = TEMPLATE.read_text().replace("{{CLASS}}", cls)
            idx.write_text(html)
        else:
            idx.write_text(
                f"<!doctype html><meta charset=utf-8><title>{cls}</title>"
                f"<h1>{cls}</h1><p>template missing at {TEMPLATE}</p>"
            )
    print(f"\033[32m✓\033[0m scaffolded {p}")
    print(f"  raw/  — drop PDFs, notes, scraped HTML")
    print(f"  site/ — rendered site (run `study serve {cls}`)")


def openclaw_chat(msg: str) -> str:
    if not msg.strip():
        return "(empty)"
    try:
        r = subprocess.run(
            ["openclaw", "agent", "--local", "--agent", "main",
             "--json", "-m", msg],
            capture_output=True, text=True, timeout=180,
        )
        if r.returncode != 0:
            return f"(openclaw exit {r.returncode}: {r.stderr[:200]})"
        d = json.loads(r.stdout)
        payloads = d.get("payloads") or []
        if payloads:
            return payloads[0].get("text") or "(empty reply)"
        return "(no payloads)"
    except subprocess.TimeoutExpired:
        return "(timeout)"
    except Exception as e:
        return f"(chat error: {e})"


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path != "/chat":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body.decode("utf-8", errors="replace"))
            msg = data.get("message", "")
        except Exception:
            msg = ""
        sys.stderr.write(f"[chat] {msg[:80]}\n")
        reply = openclaw_chat(msg)
        payload = json.dumps({"text": reply}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._cors()
        self.end_headers()
        self.wfile.write(payload)


def cmd_serve(cls: str, open_browser: bool = True):
    site = path_for(cls) / "site"
    if not site.exists():
        print(f"no site at {site}. run: study init {cls}")
        sys.exit(1)
    os.chdir(site)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        url = f"http://127.0.0.1:{PORT}/"
        print(f"\033[35m✦\033[0m study server — {cls}")
        print(f"  url:  {url}")
        print(f"  chat: POST /chat  →  openclaw main agent (MiniMax-M2.5)")
        print(f"  ctrl-c to stop")
        if open_browser:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nbye")


def cmd_list():
    if not ROOT.exists():
        print("no coursework folder yet")
        return
    classes = sorted(d for d in ROOT.iterdir() if d.is_dir())
    if not classes:
        print("no classes yet — `study init <class>` to start")
        return
    for d in classes:
        ready = (d / "site" / "index.html").exists()
        raw_n = sum(1 for _ in (d / "raw").rglob("*")) if (d / "raw").exists() else 0
        tag = "\033[32mready\033[0m" if ready else "\033[33mscaffold\033[0m"
        print(f"  {d.name:<10} {tag}   {raw_n} raw files")


def main():
    argv = sys.argv[1:]
    if not argv:
        cmd_list()
        return
    cmd, *rest = argv
    if cmd == "init" and rest:
        cmd_init(rest[0])
    elif cmd in ("serve", "open") and rest:
        cmd_serve(rest[0])
    elif cmd == "list":
        cmd_list()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
