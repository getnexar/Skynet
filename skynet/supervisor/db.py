"""SQLite database models for storing session and message data."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Session:
    """Represents a Claude Code session."""
    id: int
    session_id: str
    project_path: str
    status: str
    created_at: str
    updated_at: str


@dataclass
class Message:
    """Represents a message in a session."""
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
    """SQLite database for storing sessions and messages."""

    def __init__(self, db_path: str):
        """Initialize database with the given path.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create a database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def init(self) -> None:
        """Initialize the database by creating tables."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                project_path TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                message_uuid TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                tool_name TEXT,
                tool_input TEXT,
                tool_output TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        """)

        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_session_id
            ON sessions (session_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_status
            ON sessions (status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session_id
            ON messages (session_id)
        """)

        conn.commit()

    def create_session(self, session_id: str, project_path: str, status: str) -> Session:
        """Create a new session.

        Args:
            session_id: Unique identifier for the session.
            project_path: Path to the project directory.
            status: Current status of the session.

        Returns:
            The created Session object.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        cursor.execute("""
            INSERT INTO sessions (session_id, project_path, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, project_path, status, now, now))

        conn.commit()

        return Session(
            id=cursor.lastrowid,
            session_id=session_id,
            project_path=project_path,
            status=status,
            created_at=now,
            updated_at=now
        )

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by its session_id.

        Args:
            session_id: The session identifier to look up.

        Returns:
            The Session object if found, None otherwise.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, session_id, project_path, status, created_at, updated_at
            FROM sessions
            WHERE session_id = ?
        """, (session_id,))

        row = cursor.fetchone()
        if row is None:
            return None

        return Session(
            id=row["id"],
            session_id=row["session_id"],
            project_path=row["project_path"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def list_sessions(self, status: Optional[str] = None) -> list[Session]:
        """List all sessions, optionally filtered by status.

        Args:
            status: If provided, only return sessions with this status.

        Returns:
            List of Session objects.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if status is not None:
            cursor.execute("""
                SELECT id, session_id, project_path, status, created_at, updated_at
                FROM sessions
                WHERE status = ?
                ORDER BY created_at DESC
            """, (status,))
        else:
            cursor.execute("""
                SELECT id, session_id, project_path, status, created_at, updated_at
                FROM sessions
                ORDER BY created_at DESC
            """)

        rows = cursor.fetchall()
        return [
            Session(
                id=row["id"],
                session_id=row["session_id"],
                project_path=row["project_path"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in rows
        ]

    def update_session(self, session_id: str, status: str) -> Optional[Session]:
        """Update a session's status.

        Args:
            session_id: The session identifier to update.
            status: The new status value.

        Returns:
            The updated Session object if found, None otherwise.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        cursor.execute("""
            UPDATE sessions
            SET status = ?, updated_at = ?
            WHERE session_id = ?
        """, (status, now, session_id))

        conn.commit()

        if cursor.rowcount == 0:
            return None

        return self.get_session(session_id)

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        message_uuid: str,
        timestamp: str,
        tool_name: Optional[str] = None,
        tool_input: Optional[str] = None,
        tool_output: Optional[str] = None
    ) -> Message:
        """Add a message to a session.

        Args:
            session_id: The session this message belongs to.
            role: The role of the message sender (e.g., 'user', 'assistant').
            content: The message content.
            message_uuid: Unique identifier for the message.
            timestamp: ISO format timestamp of the message.
            tool_name: Optional name of tool used.
            tool_input: Optional tool input data.
            tool_output: Optional tool output data.

        Returns:
            The created Message object.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO messages (
                session_id, role, content, message_uuid, timestamp,
                tool_name, tool_input, tool_output
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, role, content, message_uuid, timestamp,
              tool_name, tool_input, tool_output))

        conn.commit()

        return Message(
            id=cursor.lastrowid,
            session_id=session_id,
            role=role,
            content=content,
            message_uuid=message_uuid,
            timestamp=timestamp,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output
        )

    def get_messages(self, session_id: str, limit: int = 100) -> list[Message]:
        """Get messages for a session.

        Args:
            session_id: The session to get messages for.
            limit: Maximum number of messages to return (default 100).

        Returns:
            List of Message objects ordered by timestamp.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, session_id, role, content, message_uuid, timestamp,
                   tool_name, tool_input, tool_output
            FROM messages
            WHERE session_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        """, (session_id, limit))

        rows = cursor.fetchall()
        return [
            Message(
                id=row["id"],
                session_id=row["session_id"],
                role=row["role"],
                content=row["content"],
                message_uuid=row["message_uuid"],
                timestamp=row["timestamp"],
                tool_name=row["tool_name"],
                tool_input=row["tool_input"],
                tool_output=row["tool_output"]
            )
            for row in rows
        ]

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
