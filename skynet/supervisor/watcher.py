import logging
from pathlib import Path
from typing import Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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
        existing = self.db.get_session(session_id)
        if not existing:
            self.db.create_session(session_id, project_path or str(file_path.parent), "active")
        messages = self.parser.parse_file(file_path)
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
