# Claude Code Session Board 📋

A curses-based TUI for browsing, searching, and resuming past Claude Code sessions.

## Features
- **Ranked session list** — sorted by line count (activity) or date
- **Fuzzy filter** — `/` to search by title or project path
- **Auto-title generation** — extracts first user message as session title
- **Background reindex** — titles cached for instant startup
- **One-key resume** — press Enter to resume any past session

## Keybindings
| Key | Action |
|---|---|
| `↑/↓` or `j/k` | Navigate |
| `l` | Sort by line count |
| `d` | Sort by date |
| `/` | Filter by title/project |
| `Enter` | Resume selected session |
| `q` | Quit |

## Architecture
```
session_board.py   ← TUI (curses)
gen_title.py       ← Background title generator
titles.json        ← Cached session titles
```

Scans `~/.claude/projects/` for `.jsonl` session files, extracts the first user message as title, caches results for fast lookup.

## Install
```bash
cp session_board.py ~/.claude/scripts/
cp gen_title.py ~/.claude/scripts/
# Run: python3 ~/.claude/scripts/session_board.py
```

## Built with
Python 3 (stdlib only). Uses `curses`, `json`, `subprocess`, `pathlib`.
