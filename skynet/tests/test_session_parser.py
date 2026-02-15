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
