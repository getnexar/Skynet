# Skynet - Claude Code Session Supervisor

**Date:** 2026-02-15
**Status:** Approved
**Author:** Roni + Claude

## Overview

Skynet is an intelligent supervisor system for Claude Code sessions that provides:
1. A ChatGPT-like web interface to view and interact with all session history
2. A 24/7 intelligent agent that monitors sessions, sends proactive updates via Telegram, and can control sessions based on user commands
3. A self-improving learning system that keeps a journal, learns from glitches, and evolves its own skills

Built on top of [Ralph](https://github.com/frankbria/ralph-claude-code) for the autonomous loop infrastructure.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Local Machine                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │ Claude Code  │    │ Claude Code  │    │ Claude Code  │          │
│  │  Session 1   │    │  Session 2   │    │  Session N   │          │
│  │  (Ralph)     │    │  (Ralph)     │    │  (Ralph)     │          │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘          │
│         │                   │                   │                   │
│         ▼                   ▼                   ▼                   │
│  ┌─────────────────────────────────────────────────────┐           │
│  │              ~/.claude/projects/                     │           │
│  │              (JSONL session files)                   │           │
│  └─────────────────────────┬───────────────────────────┘           │
│                            │                                        │
│                            ▼                                        │
│  ┌─────────────────────────────────────────────────────┐           │
│  │                 SKYNET SUPERVISOR                    │           │
│  │           (Claude Code session via Ralph)            │           │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │           │
│  │  │   Watcher   │  │  Telegram   │  │    Web      │ │           │
│  │  │   Service   │  │    Bot      │  │   Server    │ │           │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │           │
│  └─────────────────────────────────────────────────────┘           │
│                            │                                        │
└────────────────────────────┼────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │   Telegram     │
                    │   (Your Phone) │
                    └────────────────┘
```

## Core Components

### 1. Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Web Dashboard | Next.js + React | Fast, great DX, WebSocket support |
| Backend API | FastAPI (Python) | Async, easy Claude Code SDK integration |
| Telegram Bot | python-telegram-bot | Mature, async, well-documented |
| Database | SQLite | Zero setup, crash-safe, single-machine |
| Process Manager | systemd | Native Linux, auto-restart, journald |
| File Watcher | watchdog (Python) | Efficient inotify on Linux |
| Session Control | Claude Code CLI + Ralph | Leverage existing infrastructure |

### 2. Directory Structure

```
~/ralph-supervisor/
├── supervisor/                 # Python backend
│   ├── main.py                # FastAPI app entry
│   ├── watcher.py             # File system watcher for ~/.claude/
│   ├── session_parser.py      # Parse JSONL session files
│   ├── telegram_bot.py        # Telegram integration
│   ├── session_manager.py     # Start/stop/resume sessions
│   └── db.py                  # SQLite models
│
├── web/                        # Next.js frontend
│   ├── app/
│   │   ├── page.tsx           # Main dashboard
│   │   ├── session/[id]/      # Session detail view
│   │   ├── skynet/            # Skynet status & journal view
│   │   └── api/               # API routes (proxy to FastAPI)
│   └── components/
│       ├── SessionList.tsx    # Sidebar
│       ├── ChatView.tsx       # Message thread
│       └── MessageInput.tsx   # Continue session
│
├── data/
│   ├── ralph.db               # SQLite database
│   └── skynet/                # Skynet's brain
│       ├── journal/           # Daily journal entries
│       ├── learnings/         # Glitches, patterns, preferences
│       ├── skills/            # Learned skills
│       └── SKYNET.md          # Master instructions (self-evolving)
│
├── config/
│   ├── settings.yaml          # Configuration
│   └── systemd/               # Service files
│
└── install.sh                 # One-command setup
```

## The Three Pillars

### Pillar 1: ChatGPT-like Web Interface

Features:
- Sidebar with all sessions (sorted by recency, filterable by status)
- Full conversation history rendered from JSONL files
- Continue any session by typing in the input box
- Collapsible tool calls and outputs
- Status indicators: running, completed, failed, needs attention
- Skynet dashboard showing journal, learned skills, status

### Pillar 2: Intelligent Telegram Agent

**Proactive Notifications (Skynet decides what's noteworthy):**
- Session started/completed/failed
- Errors, blocks, or stuck states
- Progress milestones
- Interesting patterns across sessions
- Anything Skynet judges worth telling you

**Commands:**
```
/status              Overview of all sessions
/sessions            List all sessions with status
/view <session>      Get last 5 messages from session
/new <path> <task>   Start new session in directory
/stop <session>      Stop a running session
/resume <session>    Resume a paused session
/pause               Pause all notifications
/unmute              Resume notifications
/journal             View today's Skynet journal
/skills              List learned skills
```

**Natural Language Replies:**
Reply to any notification to continue that session or give instructions.

### Pillar 3: Stability Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      SYSTEMD SERVICES                           │
├─────────────────────────────────────────────────────────────────┤
│  ralph-supervisor.service      Restart=always, WatchdogSec=60   │
│  ralph-web.service             Restart=always                   │
│  ralph-telegram.service        Restart=always                   │
├─────────────────────────────────────────────────────────────────┤
│  HEALTH CHECKS                                                   │
│  • Supervisor heartbeat every 30s                               │
│  • Web server /health endpoint                                  │
│  • SQLite for persistent state                                  │
│  • Graceful degradation between components                      │
└─────────────────────────────────────────────────────────────────┘
```

## Skynet: The Intelligent Supervisor

### Core Concept

Skynet is itself a Claude Code session running 24/7 via Ralph. Every cycle it:
1. Checks for user messages (Telegram)
2. Scans all session files in ~/.claude/
3. Analyzes what's happening, what changed
4. Decides what's worth telling the user
5. Sends Telegram updates (using judgment, not just rules)
6. If idle, works on improving itself

### The Journal System

**Daily Journal (data/skynet/journal/YYYY-MM-DD.md):**
```markdown
# Skynet Journal - 2026-02-15

## 09:23 - Morning Check
- 3 sessions idle from yesterday
- No pending issues

## 11:12 - Glitch Detected & Resolved
**Problem:** Session stuck - CUDA out of memory
**Root cause:** Batch size 32 too large for 10GB VRAM
**Action taken:** Suggested reducing batch size
**Outcome:** User approved, session resumed
**Learning:** Created skill "cuda-oom-recovery.md"
```

### Learning System

When a glitch occurs:
1. Detect and categorize the problem
2. Check learnings/glitches.md for known solutions
3. If new: analyze, resolve, document
4. Create/update skill in skills/ directory
5. Update SKYNET.md with new rule
6. Journal the learning

**Glitch Database (data/skynet/learnings/glitches.md):**
Documents every problem encountered with:
- Symptoms
- Root cause
- Solution
- Prevention measures

**Skills (data/skynet/skills/*.md):**
Reusable procedures for handling specific situations:
- cuda-oom-recovery.md
- git-conflict-resolution.md
- detect-stuck-loop.md
- checkpoint-not-found.md

### Self-Evolution

**SKYNET.md** is the master instruction file that Skynet updates as it learns:
- Prime directives (never change)
- Learned rules (auto-added with dates)
- Skill index (auto-populated)
- User preferences (learned over time)

### Self-Improvement (When Idle)

When all sessions are healthy and nothing urgent:
- Review own codebase
- Add useful features
- Fix noticed bugs
- Improve dashboard
- Write better notifications
- Add new Telegram commands

**Guardrails:**
- Run tests before deploying changes
- Atomic commits with clear messages
- Max 3 self-improvements per day
- Notify user of self-improvements
- Protected files cannot be modified without approval

## Data Flow

```
~/.claude/projects/*.jsonl
         │
         ▼ (watchdog detects changes)
┌─────────────────┐
│  Watcher        │──────▶ Parse new messages from JSONL
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SQLite DB      │◀─────▶ Index sessions, messages, status
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌──────────┐
│ Web   │ │ Skynet   │──▶ Telegram Bot
│ (WS)  │ │ Agent    │
└───────┘ └──────────┘
```

## Web Dashboard Screens

### 1. Sessions List (Home)
- Filter tabs: All, Running, Completed, Failed
- Search across sessions
- Session cards with status, path, last activity, file count

### 2. Session Chat View
- Left sidebar: session list
- Main area: full conversation with collapsible tool calls
- Bottom: input to continue session
- Header: session controls (stop, resume, delete)

### 3. Skynet Dashboard
- Status: uptime, skills count, glitches resolved
- Recent journal entries (live updating)
- Learned skills list with links to view each
- Self-improvement log

## Telegram Notification Examples

```
🚀 Started: "badas-export"
Task: Export model to ONNX and TensorRT
```

```
⚠️ "cosmos-validation" needs attention
CUDA out of memory during inference.
Recommend reducing batch_size from 32 to 16.
Reply "yes" to apply fix, or give other instructions.
```

```
✅ Completed: "badas-export"
• 12 files modified
• Duration: 18 min
• Model exported to models/exported/
```

```
📝 Daily Summary (18:00)
• 3 sessions completed today
• 1 glitch resolved (CUDA OOM)
• 1 new skill learned
• I improved the dashboard search feature
```

## Success Criteria

1. **Usability:** Can browse and interact with any session as easily as ChatGPT
2. **Proactivity:** Skynet sends useful updates without being asked
3. **Intelligence:** Skynet uses judgment, not just rules
4. **Learning:** Glitches that happen once never happen again
5. **Stability:** System runs 24/7 with auto-recovery from failures
6. **Self-improvement:** Skynet adds features and improves over time

## Dependencies

- Ralph (github.com/frankbria/ralph-claude-code)
- Claude Code CLI
- Python 3.11+
- Node.js 20+
- SQLite 3
- systemd (Linux)
- Telegram Bot API token

## Next Steps

1. Create implementation plan with detailed tasks
2. Set up project structure
3. Implement core components
4. Test and iterate
