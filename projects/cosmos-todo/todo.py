#!/usr/bin/env python3
"""todo — Cosmos Terminal Kanban Board

Storage: ~/.todo/tasks.json
RPi sync: rsync over ssh via ~/bin/openclaw-rpi's known host
Telegram: piped through openclaw-rpi telegram (Cosmo-RPi bot)
"""
import argparse
import curses
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path.home() / ".todo"
DATA_FILE = DATA_DIR / "tasks.json"
RPI_HOST = "intersection@192.168.1.227"
BRIDGE = Path.home() / "bin" / "openclaw-rpi"

STATUSES = ["todo", "doing", "done"]
LABELS = {"todo": "TODO", "doing": "IN PROGRESS", "done": "DONE"}
ICON = {"todo": "○", "doing": "◐", "done": "●"}

R = "\033[0m"
B = "\033[1m"
D = "\033[2m"
RED = "\033[38;5;203m"
GRN = "\033[38;5;78m"
YEL = "\033[38;5;222m"
BLU = "\033[38;5;75m"
MAG = "\033[38;5;177m"
CYN = "\033[38;5;117m"
GRY = "\033[38;5;243m"
PNK = "\033[38;5;218m"

SCOL = {"todo": CYN, "doing": YEL, "done": GRN}
TAGCOL = {"life": PNK, "academic": BLU, "job": GRN, "meta": MAG, "work": RED}

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def vlen(s):
    return len(ANSI_RE.sub("", s))


def pad(s, w):
    return s + " " * max(0, w - vlen(s))


def load():
    if not DATA_FILE.exists():
        return {"next_id": 1, "tasks": []}
    try:
        return json.loads(DATA_FILE.read_text())
    except json.JSONDecodeError:
        return {"next_id": 1, "tasks": []}


def save(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(DATA_FILE)


def find(data, tid):
    for t in data["tasks"]:
        if t["id"] == tid:
            return t
    return None


def wrap(text, w):
    words = text.split()
    lines, cur = [], ""
    for wd in words:
        if len(cur) + len(wd) + (1 if cur else 0) > w:
            if cur:
                lines.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd) if cur else wd
    if cur:
        lines.append(cur)
    return lines or [""]


def format_card(t, w):
    id_s = f"{SCOL[t['status']]}{ICON[t['status']]} #{t['id']}{R}"
    header_prefix_len = vlen(id_s) + 1
    text_lines = wrap(t["text"], w - header_prefix_len)
    out = [pad(f"{id_s} {text_lines[0]}", w)]
    for ln in text_lines[1:]:
        out.append(pad("   " + ln, w))
    tag = t.get("tag") or ""
    dl = t.get("deadline") or ""
    meta_bits = []
    if tag:
        meta_bits.append(f"{TAGCOL.get(tag, GRY)}•{tag}{R}")
    if dl:
        today = datetime.now().strftime("%Y-%m-%d")
        col = RED if dl < today else GRY
        meta_bits.append(f"{col}⏰ {dl}{R}")
    if meta_bits:
        out.append(pad("   " + "  ".join(meta_bits), w))
    return out


def cmd_board(args):
    data = load()
    col_w = 36
    gap = 2
    total = col_w * 3 + gap * 2
    flt = getattr(args, "tag", None)
    cols = {s: [] for s in STATUSES}
    for t in data["tasks"]:
        if flt and flt != "all" and (t.get("tag") or "") != flt:
            continue
        cols[t["status"]].append(t)
    for s in cols:
        cols[s].sort(key=lambda x: (x.get("deadline") or "9999", x["id"]))

    now = datetime.now().strftime("%a %b %d  %H:%M")
    scope = f" · {flt}" if flt and flt != "all" else ""
    title = f"✦  COSMOS TODO BOARD{scope}  ✦   {now}"
    print()
    print(f"{B}{MAG}{title.center(total)}{R}")
    print(f"{GRY}{'━' * total}{R}")

    heads = [
        f"{B}{SCOL[s]}{pad(f' {ICON[s]} {LABELS[s]}  [{len(cols[s])}]', col_w)}{R}"
        for s in STATUSES
    ]
    print((" " * gap).join(heads))
    print((" " * gap).join(f"{SCOL[s]}{'─' * col_w}{R}" for s in STATUSES))

    blocks = []
    for s in STATUSES:
        block = []
        for t in cols[s]:
            block.extend(format_card(t, col_w))
            block.append(pad("", col_w))
        blocks.append(block)
    h = max((len(b) for b in blocks), default=0)
    for b in blocks:
        while len(b) < h:
            b.append(pad("", col_w))
    for i in range(h):
        print((" " * gap).join(blocks[j][i] for j in range(3)))

    print(f"{GRY}{'━' * total}{R}")
    total_n = sum(len(cols[s]) for s in STATUSES)
    print(
        f"{GRY}add:{R} todo add \"task\" -t tag   "
        f"{GRY}move:{R} todo start|done|back <id>   "
        f"{GRY}total:{R} {total_n}"
    )
    print()


def cmd_add(args):
    data = load()
    tid = data["next_id"]
    data["next_id"] += 1
    t = {
        "id": tid,
        "text": " ".join(args.text).strip(),
        "status": "todo",
        "tag": args.tag or "",
        "deadline": args.deadline or "",
        "created": datetime.now().strftime("%Y-%m-%d"),
    }
    data["tasks"].append(t)
    save(data)
    print(f"{GRN}✚ #{tid}{R} {t['text']}")


def _set(tid, status):
    data = load()
    t = find(data, tid)
    if not t:
        print(f"{RED}no task #{tid}{R}")
        sys.exit(1)
    t["status"] = status
    if status == "done":
        t["completed"] = datetime.now().strftime("%Y-%m-%d")
    save(data)
    print(f"{SCOL[status]}{ICON[status]} #{t['id']} → {LABELS[status]}{R}  {t['text']}")


def cmd_start(a): _set(a.id, "doing")
def cmd_done(a):  _set(a.id, "done")
def cmd_back(a):  _set(a.id, "todo")


def cmd_rm(args):
    data = load()
    before = len(data["tasks"])
    data["tasks"] = [t for t in data["tasks"] if t["id"] != args.id]
    if len(data["tasks"]) == before:
        print(f"{RED}no task #{args.id}{R}")
        sys.exit(1)
    save(data)
    print(f"{D}✖ removed #{args.id}{R}")


def cmd_edit(args):
    data = load()
    t = find(data, args.id)
    if not t:
        print(f"{RED}no task #{args.id}{R}")
        sys.exit(1)
    t["text"] = " ".join(args.text).strip()
    save(data)
    print(f"{CYN}~ #{t['id']}{R} {t['text']}")


def cmd_tag(args):
    data = load()
    t = find(data, args.id)
    if not t:
        print(f"{RED}no task #{args.id}{R}")
        sys.exit(1)
    t["tag"] = args.tag
    save(data)
    print(f"{CYN}~ #{t['id']}{R} tag → {args.tag}")


def cmd_deadline(args):
    data = load()
    t = find(data, args.id)
    if not t:
        print(f"{RED}no task #{args.id}{R}")
        sys.exit(1)
    t["deadline"] = args.date
    save(data)
    print(f"{CYN}~ #{t['id']}{R} deadline → {args.date}")


def cmd_clear(args):
    data = load()
    before = len(data["tasks"])
    data["tasks"] = [t for t in data["tasks"] if t["status"] != "done"]
    save(data)
    print(f"{D}cleared {before - len(data['tasks'])} done{R}")


def cmd_list(args):
    data = load()
    for s in STATUSES:
        ts = [t for t in data["tasks"] if t["status"] == s]
        if not ts:
            continue
        print(f"{B}{SCOL[s]}{LABELS[s]}{R}")
        for t in sorted(ts, key=lambda x: (x.get("deadline") or "9999", x["id"])):
            tag = f" [{t['tag']}]" if t.get("tag") else ""
            dl = f" ⏰{t['deadline']}" if t.get("deadline") else ""
            print(f"  #{t['id']}  {t['text']}{tag}{dl}")
    print()


def cmd_push(args):
    subprocess.run(["ssh", RPI_HOST, "mkdir -p ~/.todo"], check=False)
    r = subprocess.run(["rsync", "-a", str(DATA_FILE), f"{RPI_HOST}:.todo/tasks.json"])
    print(f"{GRN}↑ pushed to RPi{R}" if r.returncode == 0 else f"{RED}push failed{R}")


def cmd_pull(args):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["rsync", "-a", f"{RPI_HOST}:.todo/tasks.json", str(DATA_FILE)])
    print(f"{GRN}↓ pulled from RPi{R}" if r.returncode == 0 else f"{RED}pull failed{R}")


def plain_board():
    data = load()
    lines = ["📋 Cosmos Todo — " + datetime.now().strftime("%a %b %d")]
    emoji = {"todo": "⬜️", "doing": "🔄", "done": "✅"}
    for s in STATUSES:
        ts = [t for t in data["tasks"] if t["status"] == s]
        if not ts:
            continue
        lines.append(f"\n{emoji[s]} {LABELS[s]}")
        for t in sorted(ts, key=lambda x: (x.get("deadline") or "9999", x["id"])):
            tag = f" #{t['tag']}" if t.get("tag") else ""
            dl = f" ⏰{t['deadline']}" if t.get("deadline") else ""
            lines.append(f"  • {t['text']}{tag}{dl}")
    return "\n".join(lines)


def cmd_tg(args):
    if args.message:
        msg = " ".join(args.message)
    else:
        msg = plain_board()
    if not BRIDGE.exists():
        print(f"{RED}openclaw-rpi bridge not found at {BRIDGE}{R}")
        sys.exit(1)
    r = subprocess.run([str(BRIDGE), "telegram", msg])
    if r.returncode == 0:
        print(f"{GRN}→ Telegram sent via Cosmo-RPi{R}")


def cmd_today(args):
    cmd_board(args)
    class _A: message = None
    cmd_tg(_A())


# ─── TUI ───────────────────────────────────────────────────────────────────

CP_HEADER = 1
CP_TODO = 2
CP_DOING = 3
CP_DONE = 4
CP_LIFE = 5
CP_ACAD = 6
CP_JOB = 7
CP_DIM = 8
CP_ACCENT = 9

TAG_CP = {"life": CP_LIFE, "academic": CP_ACAD, "job": CP_JOB}


def _tui_init_colors():
    curses.start_color()
    try:
        curses.use_default_colors()
        bg = -1
    except curses.error:
        bg = curses.COLOR_BLACK
    curses.init_pair(CP_HEADER, 177, bg)
    curses.init_pair(CP_TODO,   117, bg)
    curses.init_pair(CP_DOING,  222, bg)
    curses.init_pair(CP_DONE,   78,  bg)
    curses.init_pair(CP_LIFE,   218, bg)
    curses.init_pair(CP_ACAD,   75,  bg)
    curses.init_pair(CP_JOB,    78,  bg)
    curses.init_pair(CP_DIM,    243, bg)
    curses.init_pair(CP_ACCENT, 203, bg)


def _tui_prompt(stdscr, label, prefill=""):
    h, w = stdscr.getmaxyx()
    curses.echo()
    curses.curs_set(1)
    stdscr.move(h - 1, 0)
    stdscr.clrtoeol()
    stdscr.addnstr(h - 1, 0, label, w - 1, curses.A_BOLD)
    stdscr.refresh()
    try:
        raw = stdscr.getstr(h - 1, len(label), w - len(label) - 2)
        out = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
    except KeyboardInterrupt:
        out = ""
    curses.noecho()
    curses.curs_set(0)
    return out.strip()


def _tui_filter_tasks(data, tag, search):
    tasks = list(data["tasks"])
    if tag and tag != "all":
        tasks = [t for t in tasks if (t.get("tag") or "") == tag]
    if search:
        s = search.lower()
        tasks = [t for t in tasks if s in t["text"].lower()]
    order = {"doing": 0, "todo": 1, "done": 2}
    tasks.sort(key=lambda t: (order[t["status"]], t.get("deadline") or "9999", t["id"]))
    return tasks


def _tui_loop(stdscr):
    _tui_init_colors()
    curses.curs_set(0)
    stdscr.keypad(True)

    state = {"tag": "all", "sel": 0, "msg": "", "search": ""}
    filters = [("1", "all"), ("2", "life"), ("3", "academic"), ("4", "job")]

    while True:
        data = load()
        tasks = _tui_filter_tasks(data, state["tag"], state["search"])
        if state["sel"] >= len(tasks):
            state["sel"] = max(0, len(tasks) - 1)

        h, w = stdscr.getmaxyx()
        stdscr.erase()

        # Header
        now = datetime.now().strftime("%a %b %d  %H:%M")
        scope = f" · {state['tag']}" if state["tag"] != "all" else ""
        title = f"✦  COSMOS TODO BOARD{scope}  ✦   {now}"
        stdscr.addnstr(0, 0, title.center(w), w,
                       curses.A_BOLD | curses.color_pair(CP_HEADER))
        stdscr.addnstr(1, 0, "─" * w, w, curses.color_pair(CP_DIM))

        # Filter tabs
        x = 2
        for key, name in filters:
            label = f" [{key}] {name} "
            active = name == state["tag"]
            attr = curses.A_BOLD | curses.A_REVERSE if active else curses.color_pair(CP_DIM)
            stdscr.addnstr(2, x, label, w - x - 1, attr)
            x += len(label) + 1
        if state["search"]:
            srch = f"/ {state['search']}"
            stdscr.addnstr(2, max(x, w - len(srch) - 2), srch, w,
                           curses.color_pair(CP_ACCENT))

        # Counts
        doing_n = sum(1 for t in tasks if t["status"] == "doing")
        todo_n  = sum(1 for t in tasks if t["status"] == "todo")
        done_n  = sum(1 for t in tasks if t["status"] == "done")
        counts = f"◐ {doing_n}   ○ {todo_n}   ● {done_n}   total {len(tasks)}"
        stdscr.addnstr(3, 2, counts, w - 4, curses.color_pair(CP_DIM))

        # Task list
        top = 5
        visible = h - top - 4
        start = 0
        if state["sel"] >= visible:
            start = state["sel"] - visible + 1

        for i in range(start, min(len(tasks), start + visible)):
            t = tasks[i]
            row = top + (i - start)
            icon = {"todo": "○", "doing": "◐", "done": "●"}[t["status"]]
            cp = {"todo": CP_TODO, "doing": CP_DOING, "done": CP_DONE}[t["status"]]
            id_str = f" {icon} #{t['id']:<3}"
            text = t["text"]
            if t["status"] == "done":
                text_attr = curses.color_pair(CP_DIM) | curses.A_DIM
            else:
                text_attr = curses.A_NORMAL
            sel_attr = curses.A_REVERSE if i == state["sel"] else curses.A_NORMAL

            # full row bg for selection
            stdscr.addnstr(row, 0, " " * w, w, sel_attr)
            stdscr.addnstr(row, 0, id_str, w, curses.color_pair(cp) | curses.A_BOLD | sel_attr)
            stdscr.addnstr(row, len(id_str) + 1, text,
                           w - len(id_str) - 20, text_attr | sel_attr)

            meta_x = w - 18
            tag = t.get("tag") or ""
            dl = t.get("deadline") or ""
            if tag:
                cp_tag = TAG_CP.get(tag, CP_DIM)
                stdscr.addnstr(row, meta_x, f"•{tag}"[:8],
                               8, curses.color_pair(cp_tag) | sel_attr)
            if dl:
                today = datetime.now().strftime("%Y-%m-%d")
                dl_cp = CP_ACCENT if dl < today else CP_DIM
                stdscr.addnstr(row, w - 12, f"⏰{dl}"[:11],
                               11, curses.color_pair(dl_cp) | sel_attr)

        # Footer
        help1 = " j/k move · space cycle · a add · d del · e edit · t tag · / search"
        help2 = " 1-4 tab · p push · P pull · T telegram · r refresh · q quit"
        stdscr.addnstr(h - 3, 0, help1[: w - 1], w - 1, curses.color_pair(CP_DIM))
        stdscr.addnstr(h - 2, 0, help2[: w - 1], w - 1, curses.color_pair(CP_DIM))
        if state["msg"]:
            stdscr.addnstr(h - 1, 0, (" " + state["msg"])[: w - 1], w - 1,
                           curses.A_BOLD | curses.color_pair(CP_ACCENT))

        stdscr.refresh()

        try:
            ch = stdscr.getch()
        except KeyboardInterrupt:
            break

        state["msg"] = ""

        if ch in (ord("q"), 27):
            break
        elif ch in (ord("j"), curses.KEY_DOWN):
            state["sel"] = min(max(0, len(tasks) - 1), state["sel"] + 1)
        elif ch in (ord("k"), curses.KEY_UP):
            state["sel"] = max(0, state["sel"] - 1)
        elif ch == curses.KEY_NPAGE:
            state["sel"] = min(max(0, len(tasks) - 1), state["sel"] + 10)
        elif ch == curses.KEY_PPAGE:
            state["sel"] = max(0, state["sel"] - 10)
        elif ch in (ord("g"),):
            state["sel"] = 0
        elif ch in (ord("G"),):
            state["sel"] = max(0, len(tasks) - 1)
        elif ch == ord("1"): state["tag"] = "all";      state["sel"] = 0
        elif ch == ord("2"): state["tag"] = "life";     state["sel"] = 0
        elif ch == ord("3"): state["tag"] = "academic"; state["sel"] = 0
        elif ch == ord("4"): state["tag"] = "job";      state["sel"] = 0
        elif ch == ord(" ") or ch in (curses.KEY_ENTER, 10, 13):
            if tasks:
                t = find(data, tasks[state["sel"]]["id"])
                cycle = {"todo": "doing", "doing": "done", "done": "todo"}
                t["status"] = cycle[t["status"]]
                if t["status"] == "done":
                    t["completed"] = datetime.now().strftime("%Y-%m-%d")
                save(data)
                state["msg"] = f"#{t['id']} → {LABELS[t['status']]}"
        elif ch == ord("a"):
            text = _tui_prompt(stdscr, "new task: ")
            if text:
                tag_in = _tui_prompt(stdscr, "tag (life/academic/job/—): ")
                data = load()
                tid = data["next_id"]; data["next_id"] += 1
                data["tasks"].append({
                    "id": tid, "text": text, "status": "todo",
                    "tag": tag_in, "deadline": "",
                    "created": datetime.now().strftime("%Y-%m-%d"),
                })
                save(data)
                state["msg"] = f"added #{tid}"
        elif ch == ord("d"):
            if tasks:
                t = tasks[state["sel"]]
                confirm = _tui_prompt(stdscr, f"delete #{t['id']} '{t['text'][:30]}'? (y/N): ")
                if confirm.lower() == "y":
                    data = load()
                    data["tasks"] = [x for x in data["tasks"] if x["id"] != t["id"]]
                    save(data)
                    state["msg"] = f"deleted #{t['id']}"
        elif ch == ord("e"):
            if tasks:
                t = tasks[state["sel"]]
                new_text = _tui_prompt(stdscr, f"edit #{t['id']}: ")
                if new_text:
                    data = load()
                    find(data, t["id"])["text"] = new_text
                    save(data)
                    state["msg"] = f"edited #{t['id']}"
        elif ch == ord("t"):
            if tasks:
                t = tasks[state["sel"]]
                new_tag = _tui_prompt(stdscr, f"tag #{t['id']} → ")
                data = load()
                find(data, t["id"])["tag"] = new_tag
                save(data)
                state["msg"] = f"#{t['id']} tag → {new_tag or '—'}"
        elif ch == ord("/"):
            state["search"] = _tui_prompt(stdscr, "/ ")
            state["sel"] = 0
        elif ch == ord("p"):
            subprocess.run([sys.argv[0], "push"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            state["msg"] = "↑ push attempted (check terminal output)"
        elif ch == ord("P"):
            subprocess.run([sys.argv[0], "pull"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            state["msg"] = "↓ pull attempted"
        elif ch == ord("T"):
            subprocess.run([sys.argv[0], "tg"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            state["msg"] = "→ telegram attempted"
        elif ch == ord("r"):
            state["msg"] = "reloaded"


def cmd_tui(args):
    try:
        curses.wrapper(_tui_loop)
    except curses.error as e:
        print(f"{RED}tui failed: {e}{R}")
        print("falling back to static board")
        cmd_board(args)


def main():
    p = argparse.ArgumentParser(prog="todo", description="Cosmos Todo Board")
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("board")
    sp.add_argument("tag", nargs="?", default=None)
    sp.set_defaults(func=cmd_board)

    for name, fn in [("list", cmd_list),
                     ("push", cmd_push), ("pull", cmd_pull),
                     ("clear", cmd_clear), ("today", cmd_today)]:
        sp = sub.add_parser(name)
        sp.set_defaults(func=fn)

    sp = sub.add_parser("add"); sp.add_argument("text", nargs="+")
    sp.add_argument("--tag", "-t"); sp.add_argument("--deadline", "-d")
    sp.set_defaults(func=cmd_add)

    for name, fn in [("start", cmd_start), ("done", cmd_done),
                     ("back", cmd_back), ("rm", cmd_rm)]:
        sp = sub.add_parser(name); sp.add_argument("id", type=int)
        sp.set_defaults(func=fn)

    sp = sub.add_parser("edit"); sp.add_argument("id", type=int)
    sp.add_argument("text", nargs="+"); sp.set_defaults(func=cmd_edit)

    sp = sub.add_parser("tag"); sp.add_argument("id", type=int)
    sp.add_argument("tag"); sp.set_defaults(func=cmd_tag)

    sp = sub.add_parser("deadline"); sp.add_argument("id", type=int)
    sp.add_argument("date"); sp.set_defaults(func=cmd_deadline)

    sp = sub.add_parser("tg"); sp.add_argument("message", nargs="*")
    sp.set_defaults(func=cmd_tg)

    sp = sub.add_parser("tui"); sp.set_defaults(func=cmd_tui)

    KNOWN = {"board", "tui", "add", "start", "done", "back", "rm", "edit",
             "tag", "deadline", "clear", "list", "push", "pull", "tg",
             "today"}
    argv = sys.argv[1:]
    if argv and argv[0] not in KNOWN and not argv[0].startswith("-"):
        argv = ["board"] + argv
    args = p.parse_args(argv)
    if not args.cmd:
        args.func = cmd_tui
    args.func(args)


if __name__ == "__main__":
    main()
