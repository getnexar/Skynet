import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock
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
