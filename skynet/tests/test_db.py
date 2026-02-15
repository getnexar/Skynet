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
