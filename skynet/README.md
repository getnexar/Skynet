# Skynet - Claude Code Session Supervisor

A real-time monitoring and management system for Claude Code sessions with Telegram notifications and a web dashboard.

## Features

- **Real-time Session Monitoring**: Watch Claude Code sessions as they happen
- **Telegram Notifications**: Get instant alerts for important events
- **Web Dashboard**: Beautiful Next.js interface to view all sessions
- **SQLite Database**: Persistent storage for session history
- **Systemd Integration**: Production-ready service files

## Quick Start

### Prerequisites

- Python 3.11 or later
- Node.js 18 or later
- npm

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/roni-goldshmidt/skynet.git
   cd skynet
   ```

2. Run the install script:
   ```bash
   ./install.sh
   ```

3. The script will:
   - Check for required dependencies
   - Create a Python virtual environment
   - Install Python dependencies
   - Install npm dependencies and build the web dashboard
   - Initialize the database
   - Prompt for Telegram configuration (optional)

### Manual Start

1. Start the API server:
   ```bash
   source .venv/bin/activate
   uvicorn supervisor.main:app --host 0.0.0.0 --port 8000
   ```

2. In another terminal, start the web dashboard:
   ```bash
   cd web && npm run start
   ```

3. Open http://localhost:3000 in your browser

### Production Deployment (systemd)

Install as system services:

```bash
sudo cp config/systemd/skynet-api.service /etc/systemd/system/
sudo cp config/systemd/skynet-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable skynet-api skynet-web
sudo systemctl start skynet-api skynet-web
```

Check status:
```bash
sudo systemctl status skynet-api skynet-web
```

View logs:
```bash
sudo journalctl -u skynet-api -f
sudo journalctl -u skynet-web -f
```

## Configuration

### Telegram Bot

To enable Telegram notifications:

1. Create a bot with [@BotFather](https://t.me/BotFather)
2. Get your Chat ID from [@userinfobot](https://t.me/userinfobot)
3. Add to `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

### Settings

Edit `config/settings.yaml` to customize:
- Watch directories
- Notification preferences
- Database location

## Project Structure

```
skynet/
├── config/
│   ├── settings.yaml      # Main configuration
│   └── systemd/           # Systemd service files
├── data/                  # Database and logs
├── supervisor/            # Python backend
│   ├── main.py           # FastAPI application
│   ├── db.py             # Database models
│   ├── session_parser.py # JSONL parser
│   ├── telegram_bot.py   # Telegram integration
│   └── watcher.py        # File watcher service
├── web/                   # Next.js frontend
│   └── src/
│       ├── app/          # App router pages
│       └── components/   # React components
├── tests/                # Test suite
├── install.sh            # Installation script
└── pyproject.toml        # Python project config
```

## API Endpoints

- `GET /api/sessions` - List all sessions
- `GET /api/sessions/{id}` - Get session details
- `GET /api/sessions/{id}/messages` - Get session messages
- `WS /ws` - WebSocket for real-time updates

## Development

Run tests:
```bash
source .venv/bin/activate
pytest
```

Run in development mode:
```bash
# API with auto-reload
uvicorn supervisor.main:app --reload --port 8000

# Web with hot reload
cd web && npm run dev
```

## License

MIT
