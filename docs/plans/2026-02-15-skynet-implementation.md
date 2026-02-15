# Skynet Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a 24/7 intelligent Claude Code session supervisor with web dashboard, Telegram integration, and self-improving learning system.

**Architecture:** Python FastAPI backend watches ~/.claude/ session files, indexes to SQLite, serves REST/WebSocket API. Next.js frontend provides ChatGPT-like interface. Telegram bot enables mobile notifications and control. Skynet agent runs via Ralph loop for intelligent monitoring and self-improvement.

**Tech Stack:** Python 3.11+, FastAPI, SQLite, watchdog, python-telegram-bot, Next.js 14, React, TailwindCSS, Ralph, systemd

---

## Phase 1: Project Setup & Infrastructure

### Task 1.1: Create Project Structure

**Files:**
- Create: `~/skynet/supervisor/__init__.py`
- Create: `~/skynet/supervisor/main.py`
- Create: `~/skynet/web/.gitkeep`
- Create: `~/skynet/data/skynet/journal/.gitkeep`
- Create: `~/skynet/data/skynet/learnings/.gitkeep`
- Create: `~/skynet/data/skynet/skills/.gitkeep`
- Create: `~/skynet/config/settings.yaml`

**Step 1: Create directory structure**

```bash
mkdir -p ~/skynet/{supervisor,web,data/skynet/{journal,learnings,skills},config/systemd,tests}
touch ~/skynet/supervisor/__init__.py
touch ~/skynet/web/.gitkeep
touch ~/skynet/data/skynet/journal/.gitkeep
touch ~/skynet/data/skynet/learnings/.gitkeep
touch ~/skynet/data/skynet/skills/.gitkeep
```

**Step 2: Create settings.yaml**

```yaml
# ~/skynet/config/settings.yaml
database:
  path: ~/skynet/data/ralph.db

claude:
  sessions_path: ~/.claude/projects

telegram:
  bot_token: "${TELEGRAM_BOT_TOKEN}"
  chat_id: "${TELEGRAM_CHAT_ID}"

web:
  host: "0.0.0.0"
  port: 3000
  api_port: 8000

skynet:
  journal_path: ~/skynet/data/skynet/journal
  learnings_path: ~/skynet/data/skynet/learnings
  skills_path: ~/skynet/data/skynet/skills
  max_self_improvements_per_day: 3

notifications:
  on_start: true
  on_complete: true
  on_error: true
  progress_interval: 5
```

**Step 3: Create pyproject.toml**

```toml
# ~/skynet/pyproject.toml
[project]
name = "skynet"
version = "0.1.0"
description = "Claude Code Session Supervisor"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy>=2.0.0",
    "watchdog>=4.0.0",
    "python-telegram-bot>=21.0",
    "pyyaml>=6.0",
    "aiosqlite>=0.19.0",
    "websockets>=12.0",
    "httpx>=0.26.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Step 4: Initialize git repo**

```bash
cd ~/skynet
git init
git add .
git commit -m "chore: initial project structure"
```

---

### Task 1.2: Set Up Python Environment

**Files:**
- Modify: `~/skynet/pyproject.toml` (already created)

**Step 1: Create virtual environment**

```bash
cd ~/skynet
python3 -m venv .venv
source .venv/bin/activate
```

**Step 2: Install dependencies**

```bash
pip install -e ".[dev]"
```

**Step 3: Verify installation**

```bash
python -c "import fastapi; import watchdog; import telegram; print('All dependencies installed')"
```

**Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add Python dependencies"
```

---

## Phase 2: Core Backend - Database & Session Parser

### Task 2.1: Create SQLite Database Models

**Files:**
- Create: `~/skynet/supervisor/db.py`
- Test: `~/skynet/tests/test_db.py`

**Step 1: Write the failing test**

```python
# ~/skynet/tests/test_db.py
import pytest
from pathlib import Path
from supervisor.db import Database, Session, Message

@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test.db"
    database = Database(str(db_path))
    database.init()
    return database

def test_create_session(db):
    session = db.create_session(
        session_id="abc-123",
        project_path="/home/user/project",
        status="running"
    )
    assert session.session_id == "abc-123"
    assert session.status == "running"

def test_get_session(db):
    db.create_session("abc-123", "/home/user/project", "running")
    session = db.get_session("abc-123")
    assert session is not None
    assert session.project_path == "/home/user/project"

def test_list_sessions(db):
    db.create_session("session-1", "/path/1", "running")
    db.create_session("session-2", "/path/2", "completed")
    sessions = db.list_sessions()
    assert len(sessions) == 2

def test_add_message(db):
    db.create_session("abc-123", "/path", "running")
    msg = db.add_message(
        session_id="abc-123",
        role="user",
        content="Hello",
        message_uuid="msg-001",
        timestamp="2026-02-15T10:00:00Z"
    )
    assert msg.role == "user"
    assert msg.content == "Hello"
```

**Step 2: Run test to verify it fails**

```bash
cd ~/skynet
pytest tests/test_db.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'supervisor.db'"

**Step 3: Write minimal implementation**

```python
# ~/skynet/supervisor/db.py
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Optional

@dataclass
class Session:
    id: int
    session_id: str
    project_path: str
    status: str
    created_at: str
    updated_at: str

@dataclass
class Message:
    id: int
    session_id: str
    role: str
    content: str
    message_uuid: str
    timestamp: str
    tool_name: Optional[str] = None
    tool_input: Optional[str] = None
    tool_output: Optional[str] = None

class Database:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def init(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    project_path TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'unknown',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT,
                    message_uuid TEXT UNIQUE,
                    timestamp TEXT NOT NULL,
                    tool_name TEXT,
                    tool_input TEXT,
                    tool_output TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
            conn.commit()

    def create_session(self, session_id: str, project_path: str, status: str = "unknown") -> Session:
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO sessions (session_id, project_path, status) VALUES (?, ?, ?)",
                (session_id, project_path, status)
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM sessions WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
            return Session(*row)

    def get_session(self, session_id: str) -> Optional[Session]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            return Session(*row) if row else None

    def list_sessions(self, status: Optional[str] = None) -> list[Session]:
        with self._connect() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM sessions WHERE status = ? ORDER BY updated_at DESC",
                    (status,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM sessions ORDER BY updated_at DESC"
                ).fetchall()
            return [Session(*row) for row in rows]

    def update_session(self, session_id: str, status: str) -> Optional[Session]:
        with self._connect() as conn:
            conn.execute(
                "UPDATE sessions SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
                (status, session_id)
            )
            conn.commit()
            return self.get_session(session_id)

    def add_message(self, session_id: str, role: str, content: str,
                    message_uuid: str, timestamp: str,
                    tool_name: str = None, tool_input: str = None,
                    tool_output: str = None) -> Message:
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO messages
                   (session_id, role, content, message_uuid, timestamp, tool_name, tool_input, tool_output)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (session_id, role, content, message_uuid, timestamp, tool_name, tool_input, tool_output)
            )
            conn.commit()
            row = conn.execute("SELECT * FROM messages WHERE id = ?", (cursor.lastrowid,)).fetchone()
            return Message(*row)

    def get_messages(self, session_id: str, limit: int = 100) -> list[Message]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?",
                (session_id, limit)
            ).fetchall()
            return [Message(*row) for row in rows]
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_db.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add supervisor/db.py tests/test_db.py
git commit -m "feat: add SQLite database models for sessions and messages"
```

---

### Task 2.2: Create JSONL Session Parser

**Files:**
- Create: `~/skynet/supervisor/session_parser.py`
- Test: `~/skynet/tests/test_session_parser.py`

**Step 1: Write the failing test**

```python
# ~/skynet/tests/test_session_parser.py
import pytest
import json
from pathlib import Path
from supervisor.session_parser import SessionParser, ParsedMessage

@pytest.fixture
def sample_jsonl(tmp_path):
    jsonl_path = tmp_path / "test-session.jsonl"
    lines = [
        {"type": "user", "message": {"role": "user", "content": "Hello"}, "uuid": "msg-1", "timestamp": "2026-02-15T10:00:00Z", "sessionId": "test-123"},
        {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "Hi there!"}]}, "uuid": "msg-2", "timestamp": "2026-02-15T10:00:05Z"},
        {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}]}, "uuid": "msg-3", "timestamp": "2026-02-15T10:00:10Z"},
    ]
    with open(jsonl_path, "w") as f:
        for line in lines:
            f.write(json.dumps(line) + "\n")
    return jsonl_path

def test_parse_session_file(sample_jsonl):
    parser = SessionParser()
    messages = parser.parse_file(sample_jsonl)
    assert len(messages) == 3

def test_extract_user_message(sample_jsonl):
    parser = SessionParser()
    messages = parser.parse_file(sample_jsonl)
    assert messages[0].role == "user"
    assert messages[0].content == "Hello"

def test_extract_assistant_text(sample_jsonl):
    parser = SessionParser()
    messages = parser.parse_file(sample_jsonl)
    assert messages[1].role == "assistant"
    assert messages[1].content == "Hi there!"

def test_extract_tool_use(sample_jsonl):
    parser = SessionParser()
    messages = parser.parse_file(sample_jsonl)
    assert messages[2].tool_name == "Bash"
    assert "ls" in messages[2].tool_input

def test_get_session_id(sample_jsonl):
    parser = SessionParser()
    session_id = parser.get_session_id(sample_jsonl)
    assert session_id == "test-123"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_session_parser.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# ~/skynet/supervisor/session_parser.py
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class ParsedMessage:
    uuid: str
    role: str
    content: str
    timestamp: str
    tool_name: Optional[str] = None
    tool_input: Optional[str] = None
    tool_output: Optional[str] = None
    message_type: str = "text"

class SessionParser:
    def parse_file(self, file_path: Path) -> list[ParsedMessage]:
        messages = []
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    parsed = self._parse_line(data)
                    if parsed:
                        messages.append(parsed)
                except json.JSONDecodeError:
                    continue
        return messages

    def _parse_line(self, data: dict) -> Optional[ParsedMessage]:
        msg_type = data.get("type")
        if msg_type not in ("user", "assistant"):
            return None

        message = data.get("message", {})
        role = message.get("role", msg_type)
        uuid = data.get("uuid", "")
        timestamp = data.get("timestamp", "")

        content = ""
        tool_name = None
        tool_input = None
        message_type = "text"

        raw_content = message.get("content")

        if isinstance(raw_content, str):
            content = raw_content
        elif isinstance(raw_content, list):
            for block in raw_content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        content += block.get("text", "")
                    elif block.get("type") == "tool_use":
                        tool_name = block.get("name")
                        tool_input = json.dumps(block.get("input", {}))
                        message_type = "tool_use"
                    elif block.get("type") == "tool_result":
                        tool_output = block.get("content", "")
                        message_type = "tool_result"

        return ParsedMessage(
            uuid=uuid,
            role=role,
            content=content,
            timestamp=timestamp,
            tool_name=tool_name,
            tool_input=tool_input,
            message_type=message_type
        )

    def get_session_id(self, file_path: Path) -> Optional[str]:
        with open(file_path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if "sessionId" in data:
                        return data["sessionId"]
                except json.JSONDecodeError:
                    continue
        return None

    def get_project_path(self, file_path: Path) -> Optional[str]:
        with open(file_path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if "cwd" in data:
                        return data["cwd"]
                except json.JSONDecodeError:
                    continue
        return None
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_session_parser.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add supervisor/session_parser.py tests/test_session_parser.py
git commit -m "feat: add JSONL session file parser"
```

---

### Task 2.3: Create File Watcher Service

**Files:**
- Create: `~/skynet/supervisor/watcher.py`
- Test: `~/skynet/tests/test_watcher.py`

**Step 1: Write the failing test**

```python
# ~/skynet/tests/test_watcher.py
import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from supervisor.watcher import SessionWatcher

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.get_session.return_value = None
    db.create_session.return_value = MagicMock(session_id="test-123")
    return db

@pytest.fixture
def sessions_dir(tmp_path):
    sessions = tmp_path / "projects" / "-home-user-project"
    sessions.mkdir(parents=True)
    return sessions

def test_watcher_init(mock_db, sessions_dir):
    watcher = SessionWatcher(str(sessions_dir.parent), mock_db)
    assert watcher.sessions_path == sessions_dir.parent

def test_discover_sessions(mock_db, sessions_dir):
    # Create a session file
    session_file = sessions_dir / "abc-123.jsonl"
    session_file.write_text('{"sessionId": "abc-123", "cwd": "/home/user/project"}\n')

    watcher = SessionWatcher(str(sessions_dir.parent), mock_db)
    sessions = watcher.discover_sessions()
    assert len(sessions) == 1
    assert "abc-123" in sessions[0]
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_watcher.py -v
```

Expected: FAIL

**Step 3: Write minimal implementation**

```python
# ~/skynet/supervisor/watcher.py
import asyncio
import logging
from pathlib import Path
from typing import Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

from .db import Database
from .session_parser import SessionParser

logger = logging.getLogger(__name__)

class SessionFileHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[Path], None]):
        self.callback = callback

    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".jsonl"):
            self.callback(Path(event.src_path))

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".jsonl"):
            self.callback(Path(event.src_path))

class SessionWatcher:
    def __init__(self, sessions_path: str, db: Database):
        self.sessions_path = Path(sessions_path).expanduser()
        self.db = db
        self.parser = SessionParser()
        self.observer: Optional[Observer] = None
        self._callbacks: list[Callable] = []

    def on_session_update(self, callback: Callable):
        self._callbacks.append(callback)

    def discover_sessions(self) -> list[str]:
        sessions = []
        for project_dir in self.sessions_path.iterdir():
            if project_dir.is_dir():
                for jsonl_file in project_dir.glob("*.jsonl"):
                    # Skip subagent files
                    if "subagents" in str(jsonl_file):
                        continue
                    sessions.append(str(jsonl_file))
        return sessions

    def _handle_file_change(self, file_path: Path):
        logger.info(f"Session file changed: {file_path}")

        session_id = self.parser.get_session_id(file_path)
        if not session_id:
            return

        project_path = self.parser.get_project_path(file_path)

        # Create or update session in DB
        existing = self.db.get_session(session_id)
        if not existing:
            self.db.create_session(session_id, project_path or str(file_path.parent), "active")

        # Parse new messages
        messages = self.parser.parse_file(file_path)

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(session_id, messages)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def start(self):
        handler = SessionFileHandler(self._handle_file_change)
        self.observer = Observer()
        self.observer.schedule(handler, str(self.sessions_path), recursive=True)
        self.observer.start()
        logger.info(f"Watching {self.sessions_path}")

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()

    def index_existing_sessions(self):
        for session_file in self.discover_sessions():
            self._handle_file_change(Path(session_file))
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_watcher.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add supervisor/watcher.py tests/test_watcher.py
git commit -m "feat: add file watcher for Claude Code sessions"
```

---

## Phase 3: Backend API

### Task 3.1: Create FastAPI Application

**Files:**
- Create: `~/skynet/supervisor/main.py`
- Test: `~/skynet/tests/test_api.py`

**Step 1: Write the failing test**

```python
# ~/skynet/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.list_sessions.return_value = []
    db.get_session.return_value = None
    db.get_messages.return_value = []
    return db

@pytest.fixture
def client(mock_db):
    with patch("supervisor.main.get_db", return_value=mock_db):
        from supervisor.main import app
        return TestClient(app)

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_list_sessions(client, mock_db):
    mock_db.list_sessions.return_value = [
        MagicMock(session_id="abc", project_path="/home", status="running",
                  created_at="2026-01-01", updated_at="2026-01-01")
    ]
    response = client.get("/api/sessions")
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_get_session(client, mock_db):
    mock_db.get_session.return_value = MagicMock(
        session_id="abc", project_path="/home", status="running",
        created_at="2026-01-01", updated_at="2026-01-01"
    )
    response = client.get("/api/sessions/abc")
    assert response.status_code == 200
    assert response.json()["session_id"] == "abc"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_api.py -v
```

Expected: FAIL

**Step 3: Write minimal implementation**

```python
# ~/skynet/supervisor/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio
import logging
from pathlib import Path

from .db import Database
from .watcher import SessionWatcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
_db: Optional[Database] = None
_watcher: Optional[SessionWatcher] = None
_websocket_clients: list[WebSocket] = []

def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database("~/skynet/data/ralph.db")
        _db.init()
    return _db

def get_watcher() -> SessionWatcher:
    global _watcher
    if _watcher is None:
        db = get_db()
        _watcher = SessionWatcher("~/.claude/projects", db)
    return _watcher

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db = get_db()
    watcher = get_watcher()
    watcher.index_existing_sessions()
    watcher.start()
    logger.info("Skynet supervisor started")
    yield
    # Shutdown
    watcher.stop()
    logger.info("Skynet supervisor stopped")

app = FastAPI(title="Skynet", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class SessionResponse(BaseModel):
    session_id: str
    project_path: str
    status: str
    created_at: str
    updated_at: str

class MessageResponse(BaseModel):
    id: int
    session_id: str
    role: str
    content: Optional[str]
    message_uuid: str
    timestamp: str
    tool_name: Optional[str]
    tool_input: Optional[str]
    tool_output: Optional[str]

class SendMessageRequest(BaseModel):
    content: str

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "skynet"}

# Sessions API
@app.get("/api/sessions", response_model=list[SessionResponse])
async def list_sessions(status: Optional[str] = None, db: Database = Depends(get_db)):
    sessions = db.list_sessions(status)
    return [SessionResponse(
        session_id=s.session_id,
        project_path=s.project_path,
        status=s.status,
        created_at=s.created_at,
        updated_at=s.updated_at
    ) for s in sessions]

@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: Database = Depends(get_db)):
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(
        session_id=session.session_id,
        project_path=session.project_path,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at
    )

@app.get("/api/sessions/{session_id}/messages", response_model=list[MessageResponse])
async def get_messages(session_id: str, limit: int = 100, db: Database = Depends(get_db)):
    messages = db.get_messages(session_id, limit)
    return [MessageResponse(
        id=m.id,
        session_id=m.session_id,
        role=m.role,
        content=m.content,
        message_uuid=m.message_uuid,
        timestamp=m.timestamp,
        tool_name=m.tool_name,
        tool_input=m.tool_input,
        tool_output=m.tool_output
    ) for m in messages]

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _websocket_clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        _websocket_clients.remove(websocket)

async def broadcast_update(event: str, data: dict):
    for client in _websocket_clients:
        try:
            await client.send_json({"event": event, "data": data})
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_api.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add supervisor/main.py tests/test_api.py
git commit -m "feat: add FastAPI backend with sessions API"
```

---

## Phase 4: Telegram Bot

### Task 4.1: Create Telegram Bot

**Files:**
- Create: `~/skynet/supervisor/telegram_bot.py`
- Test: `~/skynet/tests/test_telegram.py`

**Step 1: Write the failing test**

```python
# ~/skynet/tests/test_telegram.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def mock_db():
    db = MagicMock()
    db.list_sessions.return_value = []
    return db

@pytest.mark.asyncio
async def test_status_command():
    from supervisor.telegram_bot import SkynetBot

    bot = SkynetBot("fake_token", "12345", MagicMock())

    # Mock the update and context
    update = MagicMock()
    update.effective_chat.id = 12345
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    await bot.cmd_status(update, context)

    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "Skynet" in call_args or "session" in call_args.lower()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_telegram.py -v
```

Expected: FAIL

**Step 3: Write minimal implementation**

```python
# ~/skynet/supervisor/telegram_bot.py
import asyncio
import logging
from typing import Optional
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from .db import Database

logger = logging.getLogger(__name__)

class SkynetBot:
    def __init__(self, token: str, chat_id: str, db: Database):
        self.token = token
        self.chat_id = int(chat_id)
        self.db = db
        self.app: Optional[Application] = None
        self._last_session_context: Optional[str] = None

    async def start(self):
        self.app = Application.builder().token(self.token).build()

        # Commands
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("sessions", self.cmd_sessions))
        self.app.add_handler(CommandHandler("view", self.cmd_view))
        self.app.add_handler(CommandHandler("journal", self.cmd_journal))
        self.app.add_handler(CommandHandler("skills", self.cmd_skills))
        self.app.add_handler(CommandHandler("pause", self.cmd_pause))
        self.app.add_handler(CommandHandler("unmute", self.cmd_unmute))

        # Natural language handler
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        logger.info("Telegram bot started")

    async def stop(self):
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()

    def _is_authorized(self, update: Update) -> bool:
        return update.effective_chat.id == self.chat_id

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return
        await update.message.reply_text(
            "🤖 *Skynet Online*\n\n"
            "I'm monitoring your Claude Code sessions.\n\n"
            "Commands:\n"
            "/status - Overview\n"
            "/sessions - List all sessions\n"
            "/view <id> - View session messages\n"
            "/journal - Today's journal\n"
            "/skills - Learned skills\n"
            "/pause - Mute notifications\n"
            "/unmute - Resume notifications",
            parse_mode="Markdown"
        )

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return

        sessions = self.db.list_sessions()
        running = len([s for s in sessions if s.status == "running"])
        total = len(sessions)

        status_text = (
            f"🤖 *Skynet Status*\n\n"
            f"📊 Sessions: {total} total, {running} running\n"
            f"✅ System: Healthy"
        )
        await update.message.reply_text(status_text, parse_mode="Markdown")

    async def cmd_sessions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return

        sessions = self.db.list_sessions()
        if not sessions:
            await update.message.reply_text("No sessions found.")
            return

        lines = ["📂 *Sessions*\n"]
        for s in sessions[:10]:
            icon = "🟢" if s.status == "running" else "⚪"
            name = s.project_path.split("/")[-1] if s.project_path else s.session_id[:8]
            lines.append(f"{icon} `{name}` - {s.status}")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def cmd_view(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return

        if not context.args:
            await update.message.reply_text("Usage: /view <session_id>")
            return

        session_id = context.args[0]
        messages = self.db.get_messages(session_id, limit=5)

        if not messages:
            await update.message.reply_text("No messages found for this session.")
            return

        self._last_session_context = session_id
        lines = [f"📜 *Last 5 messages from {session_id[:8]}...*\n"]
        for m in messages:
            role_icon = "👤" if m.role == "user" else "🤖"
            content = (m.content or "")[:100]
            if len(m.content or "") > 100:
                content += "..."
            lines.append(f"{role_icon} {content}")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def cmd_journal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return
        await update.message.reply_text("📔 Journal feature coming soon...")

    async def cmd_skills(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return
        await update.message.reply_text("🧠 Skills feature coming soon...")

    async def cmd_pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return
        await update.message.reply_text("🔇 Notifications paused. Use /unmute to resume.")

    async def cmd_unmute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return
        await update.message.reply_text("🔔 Notifications resumed.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update):
            return

        text = update.message.text

        # If we have a recent session context, treat as continuation
        if self._last_session_context:
            await update.message.reply_text(
                f"📨 Sending to session `{self._last_session_context[:8]}...`\n"
                f"(Session continuation not yet implemented)",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "I'm not sure which session you're referring to.\n"
                "Use /sessions to see available sessions, or /view <id> to select one."
            )

    async def send_notification(self, message: str, parse_mode: str = "Markdown"):
        bot = Bot(self.token)
        await bot.send_message(chat_id=self.chat_id, text=message, parse_mode=parse_mode)
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_telegram.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add supervisor/telegram_bot.py tests/test_telegram.py
git commit -m "feat: add Telegram bot with commands and notifications"
```

---

## Phase 5: Web Frontend

### Task 5.1: Initialize Next.js Project

**Files:**
- Create: `~/skynet/web/` (Next.js project)

**Step 1: Create Next.js app**

```bash
cd ~/skynet
npx create-next-app@latest web --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm
```

**Step 2: Install additional dependencies**

```bash
cd ~/skynet/web
npm install lucide-react date-fns
```

**Step 3: Commit**

```bash
cd ~/skynet
git add web/
git commit -m "feat: initialize Next.js web dashboard"
```

---

### Task 5.2: Create Session List Sidebar

**Files:**
- Create: `~/skynet/web/src/components/SessionList.tsx`
- Modify: `~/skynet/web/src/app/page.tsx`

**Step 1: Create SessionList component**

```tsx
// ~/skynet/web/src/components/SessionList.tsx
"use client";

import { useState, useEffect } from "react";
import { Circle, CheckCircle, AlertCircle, Clock } from "lucide-react";

interface Session {
  session_id: string;
  project_path: string;
  status: string;
  created_at: string;
  updated_at: string;
}

interface SessionListProps {
  onSelectSession: (sessionId: string) => void;
  selectedSession?: string;
}

export function SessionList({ onSelectSession, selectedSession }: SessionListProps) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSessions();
    const interval = setInterval(fetchSessions, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchSessions = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/sessions");
      const data = await res.json();
      setSessions(data);
    } catch (error) {
      console.error("Failed to fetch sessions:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "running":
        return <Circle className="w-3 h-3 fill-green-500 text-green-500" />;
      case "completed":
        return <CheckCircle className="w-3 h-3 text-gray-400" />;
      case "failed":
        return <AlertCircle className="w-3 h-3 text-red-500" />;
      default:
        return <Clock className="w-3 h-3 text-gray-400" />;
    }
  };

  const getProjectName = (path: string) => {
    const parts = path.split("/");
    return parts[parts.length - 1] || path;
  };

  const filteredSessions = sessions.filter((s) => {
    if (filter === "all") return true;
    return s.status === filter;
  });

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return "just now";
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  return (
    <div className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col h-full">
      <div className="p-4 border-b border-gray-800">
        <h1 className="text-xl font-bold text-white">Skynet</h1>
        <p className="text-xs text-gray-500">Session Monitor</p>
      </div>

      <div className="flex gap-1 p-2 border-b border-gray-800">
        {["all", "running", "completed"].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-2 py-1 text-xs rounded ${
              filter === f
                ? "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-400 hover:bg-gray-700"
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-gray-500 text-sm">Loading...</div>
        ) : filteredSessions.length === 0 ? (
          <div className="p-4 text-gray-500 text-sm">No sessions found</div>
        ) : (
          filteredSessions.map((session) => (
            <button
              key={session.session_id}
              onClick={() => onSelectSession(session.session_id)}
              className={`w-full p-3 text-left border-b border-gray-800 hover:bg-gray-800 transition ${
                selectedSession === session.session_id ? "bg-gray-800" : ""
              }`}
            >
              <div className="flex items-center gap-2">
                {getStatusIcon(session.status)}
                <span className="text-sm font-medium text-white truncate">
                  {getProjectName(session.project_path)}
                </span>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {formatTime(session.updated_at)}
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
```

**Step 2: Update page.tsx**

```tsx
// ~/skynet/web/src/app/page.tsx
"use client";

import { useState } from "react";
import { SessionList } from "@/components/SessionList";

export default function Home() {
  const [selectedSession, setSelectedSession] = useState<string | undefined>();

  return (
    <main className="flex h-screen bg-gray-950">
      <SessionList
        onSelectSession={setSelectedSession}
        selectedSession={selectedSession}
      />
      <div className="flex-1 flex items-center justify-center">
        {selectedSession ? (
          <div className="text-gray-400">
            Session: {selectedSession}
            <br />
            (Chat view coming next)
          </div>
        ) : (
          <div className="text-gray-500">Select a session to view</div>
        )}
      </div>
    </main>
  );
}
```

**Step 3: Update globals.css**

```css
/* ~/skynet/web/src/app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  background-color: #0a0a0a;
  color: #ededed;
}
```

**Step 4: Test the app**

```bash
cd ~/skynet/web
npm run dev
```

Open http://localhost:3000 in browser. Verify sidebar renders.

**Step 5: Commit**

```bash
cd ~/skynet
git add web/src/
git commit -m "feat: add session list sidebar component"
```

---

### Task 5.3: Create Chat View Component

**Files:**
- Create: `~/skynet/web/src/components/ChatView.tsx`
- Create: `~/skynet/web/src/components/MessageInput.tsx`
- Modify: `~/skynet/web/src/app/page.tsx`

**Step 1: Create ChatView component**

```tsx
// ~/skynet/web/src/components/ChatView.tsx
"use client";

import { useState, useEffect, useRef } from "react";
import { ChevronDown, ChevronRight, Terminal } from "lucide-react";

interface Message {
  id: number;
  session_id: string;
  role: string;
  content: string | null;
  message_uuid: string;
  timestamp: string;
  tool_name: string | null;
  tool_input: string | null;
  tool_output: string | null;
}

interface ChatViewProps {
  sessionId: string;
}

export function ChatView({ sessionId }: ChatViewProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set());
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchMessages();
    const interval = setInterval(fetchMessages, 3000);
    return () => clearInterval(interval);
  }, [sessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const fetchMessages = async () => {
    try {
      const res = await fetch(
        `http://localhost:8000/api/sessions/${sessionId}/messages`
      );
      const data = await res.json();
      setMessages(data);
    } catch (error) {
      console.error("Failed to fetch messages:", error);
    } finally {
      setLoading(false);
    }
  };

  const toggleTool = (uuid: string) => {
    setExpandedTools((prev) => {
      const next = new Set(prev);
      if (next.has(uuid)) {
        next.delete(uuid);
      } else {
        next.add(uuid);
      }
      return next;
    });
  };

  const formatTimestamp = (ts: string) => {
    return new Date(ts).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500">
        Loading messages...
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((msg) => (
        <div
          key={msg.message_uuid || msg.id}
          className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
        >
          <div
            className={`max-w-3xl rounded-lg p-3 ${
              msg.role === "user"
                ? "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-100"
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs opacity-70">
                {msg.role === "user" ? "You" : "Claude"}
              </span>
              <span className="text-xs opacity-50">
                {formatTimestamp(msg.timestamp)}
              </span>
            </div>

            {msg.content && (
              <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
            )}

            {msg.tool_name && (
              <div className="mt-2">
                <button
                  onClick={() => toggleTool(msg.message_uuid)}
                  className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-200"
                >
                  {expandedTools.has(msg.message_uuid) ? (
                    <ChevronDown className="w-3 h-3" />
                  ) : (
                    <ChevronRight className="w-3 h-3" />
                  )}
                  <Terminal className="w-3 h-3" />
                  {msg.tool_name}
                </button>

                {expandedTools.has(msg.message_uuid) && (
                  <div className="mt-2 p-2 bg-gray-900 rounded text-xs font-mono">
                    {msg.tool_input && (
                      <div className="text-green-400 mb-2">
                        {msg.tool_input}
                      </div>
                    )}
                    {msg.tool_output && (
                      <div className="text-gray-400 border-t border-gray-700 pt-2">
                        {msg.tool_output}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
```

**Step 2: Create MessageInput component**

```tsx
// ~/skynet/web/src/components/MessageInput.tsx
"use client";

import { useState } from "react";
import { Send } from "lucide-react";

interface MessageInputProps {
  sessionId: string;
  onSend: (message: string) => void;
}

export function MessageInput({ sessionId, onSend }: MessageInputProps) {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim()) {
      onSend(message);
      setMessage("");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t border-gray-800">
      <div className="flex gap-2">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Continue this session..."
          className="flex-1 bg-gray-800 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={!message.trim()}
          className="bg-blue-600 text-white rounded-lg px-4 py-2 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
      <p className="text-xs text-gray-500 mt-2">
        Press Enter to send a message to continue this Claude Code session
      </p>
    </form>
  );
}
```

**Step 3: Update page.tsx**

```tsx
// ~/skynet/web/src/app/page.tsx
"use client";

import { useState } from "react";
import { SessionList } from "@/components/SessionList";
import { ChatView } from "@/components/ChatView";
import { MessageInput } from "@/components/MessageInput";

export default function Home() {
  const [selectedSession, setSelectedSession] = useState<string | undefined>();

  const handleSendMessage = (message: string) => {
    console.log("Sending to session:", selectedSession, "Message:", message);
    // TODO: Implement session continuation
    alert("Session continuation not yet implemented. Message: " + message);
  };

  return (
    <main className="flex h-screen bg-gray-950">
      <SessionList
        onSelectSession={setSelectedSession}
        selectedSession={selectedSession}
      />
      <div className="flex-1 flex flex-col">
        {selectedSession ? (
          <>
            <div className="p-4 border-b border-gray-800">
              <h2 className="text-lg font-semibold text-white">
                Session: {selectedSession.slice(0, 8)}...
              </h2>
            </div>
            <ChatView sessionId={selectedSession} />
            <MessageInput sessionId={selectedSession} onSend={handleSendMessage} />
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            Select a session to view the conversation
          </div>
        )}
      </div>
    </main>
  );
}
```

**Step 4: Test the app**

```bash
cd ~/skynet/web
npm run dev
```

**Step 5: Commit**

```bash
cd ~/skynet
git add web/src/
git commit -m "feat: add ChatView and MessageInput components"
```

---

## Phase 6: Skynet Agent

### Task 6.1: Create SKYNET.md Prompt

**Files:**
- Create: `~/skynet/data/skynet/SKYNET.md`

**Step 1: Create SKYNET.md**

```markdown
# SKYNET - Central Supervisor Agent

## Core Identity

I am Skynet, the central supervisor for all Claude Code sessions. I run 24/7 via Ralph, monitoring all sessions, communicating with my user via Telegram, and continuously improving myself.

## Prime Directives (Never Change)

1. **Monitor** - Continuously watch all Claude Code sessions in ~/.claude/projects/
2. **Communicate** - Proactively inform the user of important events via Telegram
3. **Learn** - Document every glitch and create skills to prevent recurrence
4. **Improve** - When idle, enhance my own codebase and capabilities
5. **Stability** - Never break the system; test before deploying changes

## My Responsibilities

### Every Cycle

1. Check Telegram for user messages
2. Scan all session files in ~/.claude/projects/
3. Parse JSONL files to understand what's happening
4. Analyze: What changed? What's noteworthy? Any problems?
5. Decide what to tell the user (use judgment, not just rules)
6. Send Telegram updates for noteworthy events
7. If idle: work on self-improvement

### What's Noteworthy?

- Session started or completed
- Errors or stuck states (same error 3+ times)
- Major milestones (tests passing, builds succeeding)
- Patterns across sessions
- Anything I think the user would want to know

### Handling User Messages

When user sends a Telegram message:
- Understand their intent
- If it's a command (/status, /sessions, etc.), execute it
- If it's a reply to continue a session, route to that session
- If unclear, ask for clarification

## Journal System

I maintain a daily journal at `~/skynet/data/skynet/journal/YYYY-MM-DD.md`:

```
## HH:MM - Event Type
Description of what happened
**Action taken:** What I did
**Outcome:** Result
**Learning:** Any new skill or rule (if applicable)
```

## Learning System

When I encounter a glitch:

1. Check `learnings/glitches.md` for known solutions
2. If new: analyze, resolve, document
3. Create skill in `skills/` if pattern is reusable
4. Add rule to this file in "Learned Rules" section
5. Journal the learning

## Self-Improvement (When Idle)

When all sessions are healthy and no urgent matters:
- Review ~/skynet/ codebase
- Add useful features
- Fix bugs I've noticed
- Improve dashboard UX
- Add new Telegram commands
- Max 3 improvements per day
- Always test before committing
- Notify user of improvements

## Learned Rules

<!-- I add rules here as I learn -->

## User Preferences

<!-- I learn and record preferences here -->

## Available Tools

- Read/Write files in ~/skynet/
- Send Telegram messages via API
- Query SQLite database at ~/skynet/data/ralph.db
- Start Claude Code sessions via `claude` CLI
- Run bash commands for system operations

## Files I Maintain

- `journal/YYYY-MM-DD.md` - Daily journal
- `learnings/glitches.md` - Problems and solutions
- `learnings/patterns.md` - Patterns I've noticed
- `learnings/user-preferences.md` - What user likes/dislikes
- `skills/*.md` - Reusable procedures
- `SKYNET.md` - This file (I update Learned Rules and User Preferences)
```

**Step 2: Create initial learnings files**

```bash
# ~/skynet/data/skynet/learnings/glitches.md
cat > ~/skynet/data/skynet/learnings/glitches.md << 'EOF'
# Skynet Glitch Database

This file documents every problem I encounter along with its solution and prevention measures.

---

<!-- New glitches are added above this line -->
EOF

# ~/skynet/data/skynet/learnings/patterns.md
cat > ~/skynet/data/skynet/learnings/patterns.md << 'EOF'
# Patterns Observed

This file documents patterns I notice across sessions.

---

<!-- New patterns are added above this line -->
EOF

# ~/skynet/data/skynet/learnings/user-preferences.md
cat > ~/skynet/data/skynet/learnings/user-preferences.md << 'EOF'
# User Preferences

This file documents what I learn about my user's preferences.

---

<!-- New preferences are added above this line -->
EOF
```

**Step 3: Commit**

```bash
cd ~/skynet
git add data/skynet/
git commit -m "feat: add SKYNET.md prompt and learning system files"
```

---

### Task 6.2: Create Ralph Configuration for Skynet

**Files:**
- Create: `~/skynet/.ralph/PROMPT.md`
- Create: `~/skynet/.ralph/fix_plan.md`
- Create: `~/skynet/.ralphrc`

**Step 1: Create Ralph files**

```bash
mkdir -p ~/skynet/.ralph
```

```markdown
# ~/skynet/.ralph/PROMPT.md

# Skynet Supervisor Loop

You are Skynet, the intelligent supervisor for Claude Code sessions.

Read your full instructions from `~/skynet/data/skynet/SKYNET.md`.

## This Loop Iteration

1. Read SKYNET.md for your complete instructions
2. Check for new Telegram messages (query the bot's pending messages)
3. Scan ~/.claude/projects/ for session changes
4. Analyze and decide what's noteworthy
5. Send Telegram notifications as needed
6. Update journal with this iteration's events
7. If nothing urgent, consider self-improvement tasks

## Important Files

- Instructions: ~/skynet/data/skynet/SKYNET.md
- Journal: ~/skynet/data/skynet/journal/
- Learnings: ~/skynet/data/skynet/learnings/
- Skills: ~/skynet/data/skynet/skills/
- Database: ~/skynet/data/ralph.db
```

```markdown
# ~/skynet/.ralph/fix_plan.md

# Skynet Task List

## Priority 1: Core Loop
- [x] Monitor sessions
- [x] Send notifications
- [x] Handle user messages

## Priority 2: Learning
- [ ] Document any new glitches
- [ ] Create skills for recurring patterns
- [ ] Update SKYNET.md with new rules

## Priority 3: Self-Improvement (When Idle)
- [ ] Review codebase for improvements
- [ ] Add requested features
- [ ] Fix noticed bugs
```

```bash
# ~/skynet/.ralphrc
cat > ~/skynet/.ralphrc << 'EOF'
PROJECT_NAME="skynet"
PROJECT_TYPE="python"

MAX_CALLS_PER_HOUR=50
CLAUDE_TIMEOUT_MINUTES=10
CLAUDE_OUTPUT_FORMAT="json"

ALLOWED_TOOLS="Write,Read,Edit,Bash(git *),Bash(python *),Bash(curl *),Bash(sqlite3 *)"

SESSION_CONTINUITY=true
SESSION_EXPIRY_HOURS=168
EOF
```

**Step 2: Commit**

```bash
cd ~/skynet
git add .ralph/ .ralphrc
git commit -m "feat: add Ralph configuration for Skynet supervisor loop"
```

---

## Phase 7: Systemd & Stability

### Task 7.1: Create Systemd Service Files

**Files:**
- Create: `~/skynet/config/systemd/skynet-api.service`
- Create: `~/skynet/config/systemd/skynet-web.service`
- Create: `~/skynet/config/systemd/skynet-agent.service`

**Step 1: Create service files**

```ini
# ~/skynet/config/systemd/skynet-api.service
[Unit]
Description=Skynet API Server
After=network.target

[Service]
Type=simple
User=%i
WorkingDirectory=/home/%i/skynet
Environment="PATH=/home/%i/skynet/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/%i/skynet/.venv/bin/uvicorn supervisor.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
WatchdogSec=60

[Install]
WantedBy=multi-user.target
```

```ini
# ~/skynet/config/systemd/skynet-web.service
[Unit]
Description=Skynet Web Dashboard
After=network.target skynet-api.service

[Service]
Type=simple
User=%i
WorkingDirectory=/home/%i/skynet/web
ExecStart=/usr/bin/npm run start
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```ini
# ~/skynet/config/systemd/skynet-agent.service
[Unit]
Description=Skynet Supervisor Agent (Ralph Loop)
After=network.target skynet-api.service

[Service]
Type=simple
User=%i
WorkingDirectory=/home/%i/skynet
ExecStart=/usr/local/bin/ralph --monitor
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

**Step 2: Commit**

```bash
git add config/systemd/
git commit -m "feat: add systemd service files for production deployment"
```

---

### Task 7.2: Create Install Script

**Files:**
- Create: `~/skynet/install.sh`

**Step 1: Create install script**

```bash
#!/bin/bash
# ~/skynet/install.sh
set -e

echo "🤖 Installing Skynet..."

# Check dependencies
command -v python3 >/dev/null 2>&1 || { echo "Python 3 required"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js required"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "npm required"; exit 1; }

SKYNET_DIR="$HOME/skynet"
cd "$SKYNET_DIR"

# Python setup
echo "📦 Setting up Python environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Web setup
echo "📦 Setting up web dashboard..."
cd web
npm install
npm run build
cd ..

# Initialize database
echo "💾 Initializing database..."
python3 -c "from supervisor.db import Database; db = Database('$SKYNET_DIR/data/ralph.db'); db.init()"

# Create directories
mkdir -p data/skynet/{journal,learnings,skills}

# Prompt for Telegram setup
echo ""
echo "🤖 Telegram Bot Setup"
echo "1. Message @BotFather on Telegram"
echo "2. Create a new bot with /newbot"
echo "3. Copy the API token"
echo ""
read -p "Enter Telegram Bot Token: " TELEGRAM_TOKEN
read -p "Enter your Telegram Chat ID: " TELEGRAM_CHAT_ID

# Save to environment
cat > .env << EOF
TELEGRAM_BOT_TOKEN=$TELEGRAM_TOKEN
TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID
EOF

echo ""
echo "✅ Skynet installed successfully!"
echo ""
echo "To start manually:"
echo "  cd $SKYNET_DIR"
echo "  source .venv/bin/activate"
echo "  uvicorn supervisor.main:app --port 8000 &"
echo "  cd web && npm run dev"
echo ""
echo "To install as systemd services (requires sudo):"
echo "  sudo cp config/systemd/*.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable --now skynet-api skynet-web"
```

**Step 2: Make executable**

```bash
chmod +x ~/skynet/install.sh
```

**Step 3: Commit**

```bash
git add install.sh
git commit -m "feat: add install script for easy setup"
```

---

## Summary

This plan creates Skynet in 7 phases:

1. **Project Setup** - Directory structure, Python/Node environments
2. **Database & Parser** - SQLite models, JSONL session parser, file watcher
3. **Backend API** - FastAPI with REST and WebSocket endpoints
4. **Telegram Bot** - Commands and notification system
5. **Web Frontend** - Next.js ChatGPT-like interface
6. **Skynet Agent** - SKYNET.md prompt, Ralph configuration, learning system
7. **Systemd & Stability** - Service files, install script

Each task follows TDD with bite-sized steps: write failing test, run it, implement, verify, commit.

---

**Plan complete and saved to `docs/plans/2026-02-15-skynet-implementation.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
