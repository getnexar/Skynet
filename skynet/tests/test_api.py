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
    from supervisor.main import app, get_db
    app.dependency_overrides[get_db] = lambda: mock_db
    yield TestClient(app)
    app.dependency_overrides.clear()

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
