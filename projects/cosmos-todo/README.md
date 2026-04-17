# Cosmos Todo Board 🌟

A terminal-based kanban TUI for task management, built with Python and curses.

## Features
- **Interactive TUI** — curses-based kanban board with keyboard navigation
- **3 columns**: TODO → IN PROGRESS → DONE
- **Tag filtering** — `1` all, `2` life, `3` academic, `4` job
- **RPi sync** — rsync to Raspberry Pi for cross-device access
- **Telegram notifications** — send board to phone via OpenClaw agent
- **CLI mode** — `todo add`, `todo done`, `todo start`, etc. for scripting
- **JSON storage** — lightweight, Git-friendly

## Keybindings (TUI)
| Key | Action |
|---|---|
| `j/k` | Move up/down |
| `Space` | Cycle status (TODO → DOING → DONE) |
| `a` | Add task |
| `d` | Delete task |
| `e` | Edit task |
| `t` | Change tag |
| `/` | Search |
| `1-4` | Filter by tag |
| `p/P` | Push/pull to RPi |
| `T` | Send to Telegram |
| `q` | Quit |

## Architecture
```
~/.todo/tasks.json          ← source of truth (MBA)
~/bin/openclaw-rpi telegram  ← Telegram via RPi5 bot
rsync → RPi:~/.todo/        ← cross-device sync
```

## Install
```bash
cp todo.py ~/.local/bin/todo
chmod +x ~/.local/bin/todo
mkdir -p ~/.todo
```

## Also includes: `study` CLI
Interactive study site generator + local LLM chat proxy for exam prep.
- `study init <class>` — scaffold folders
- `study serve <class>` — local server + OpenClaw chat proxy
- Generates interactive HTML study sites with Chinese annotations

## Built with
Python 3 (stdlib only — no dependencies). Uses `curses`, `argparse`, `json`, `subprocess`.
