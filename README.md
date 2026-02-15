# Skynet

**Intelligent Claude Code Session Supervisor**

A 24/7 monitoring system for Claude Code sessions with a ChatGPT-like web interface, Telegram integration, and a self-improving AI agent.

## Features

- **Web Dashboard** - ChatGPT-like interface to browse and interact with all Claude Code sessions
- **Telegram Bot** - Proactive notifications and bidirectional control from your phone
- **Intelligent Agent** - 24/7 monitoring that uses judgment, not just rules
- **Learning System** - Keeps a journal, learns from glitches, evolves its own skills
- **Self-Improvement** - Adds features and fixes bugs when idle

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Claude Code Sessions (via Ralph)                               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                           │
│  │Session 1│ │Session 2│ │Session N│                           │
│  └────┬────┘ └────┬────┘ └────┬────┘                           │
│       └───────────┼───────────┘                                 │
│                   ▼                                             │
│       ~/.claude/projects/*.jsonl                                │
│                   │                                             │
│                   ▼                                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              SKYNET SUPERVISOR                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │ Watcher  │  │ Telegram │  │   Web    │              │   │
│  │  │ Service  │  │   Bot    │  │ Dashboard│              │   │
│  │  └──────────┘  └──────────┘  └──────────┘              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                     📱 Telegram (You)
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend API | FastAPI (Python) |
| Database | SQLite |
| File Watcher | watchdog |
| Telegram Bot | python-telegram-bot |
| Web Dashboard | Next.js + React + TailwindCSS |
| Process Manager | systemd |
| Agent Loop | Ralph |

## Quick Start

```bash
# Clone the repo
git clone https://github.com/getnexar/Skynet.git
cd Skynet

# Run install script
./install.sh
```

## Documentation

- [Design Document](docs/plans/2026-02-15-skynet-design.md) - Full architecture and design
- [Implementation Plan](docs/plans/2026-02-15-skynet-implementation.md) - Detailed build plan

## Project Structure

```
~/skynet/
├── supervisor/           # Python backend
│   ├── main.py          # FastAPI app
│   ├── db.py            # SQLite models
│   ├── watcher.py       # File system watcher
│   ├── session_parser.py # JSONL parser
│   └── telegram_bot.py  # Telegram integration
├── web/                  # Next.js frontend
├── data/
│   ├── ralph.db         # SQLite database
│   └── skynet/          # Skynet's brain
│       ├── journal/     # Daily journals
│       ├── learnings/   # Glitches & patterns
│       ├── skills/      # Learned skills
│       └── SKYNET.md    # Master instructions
├── config/
│   ├── settings.yaml    # Configuration
│   └── systemd/         # Service files
└── install.sh           # Setup script
```

## Telegram Commands

```
/status    - Overview of all sessions
/sessions  - List all sessions
/view <id> - View session messages
/journal   - Today's Skynet journal
/skills    - List learned skills
/pause     - Mute notifications
/unmute    - Resume notifications
```

## The Learning System

Skynet maintains:
- **Daily Journal** - Events, decisions, outcomes
- **Glitch Database** - Problems encountered and solutions
- **Skills** - Reusable procedures for handling situations
- **Self-Evolving Instructions** - SKYNET.md updates as it learns

When a glitch occurs once, Skynet documents it and creates a skill to prevent it from ever happening again.

## License

MIT

## Built With

- [Ralph](https://github.com/frankbria/ralph-claude-code) - Autonomous AI development loop
- [Claude Code](https://claude.ai/code) - AI coding assistant by Anthropic
