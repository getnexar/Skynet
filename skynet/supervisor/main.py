"""FastAPI backend for Skynet web dashboard."""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict


# Pydantic models
class SessionResponse(BaseModel):
    """Response model for session data."""
    session_id: str
    project_path: str
    status: str
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Response model for message data."""
    id: int
    session_id: str
    role: str
    content: str
    timestamp: str

    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    service: str


# Database dependency
_db_instance = None


def get_db():
    """Get database instance for dependency injection."""
    global _db_instance
    if _db_instance is None:
        # In production, this would return the actual database instance
        # For now, return None which will be mocked in tests
        pass
    return _db_instance


def set_db(db):
    """Set database instance (for initialization)."""
    global _db_instance
    _db_instance = db


# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()

# Watcher instance (to be set during startup)
_watcher = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler for startup and shutdown events."""
    global _watcher
    # Startup: Initialize watcher if available
    # In production, this would start the file watcher
    # _watcher = Watcher()
    # await _watcher.start()
    yield
    # Shutdown: Stop watcher if running
    if _watcher is not None:
        # await _watcher.stop()
        pass


# Create FastAPI app
app = FastAPI(
    title="Skynet API",
    description="REST API backend for Skynet web dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "skynet"}


# Sessions API
@app.get("/api/sessions", response_model=List[SessionResponse])
async def list_sessions(db=Depends(get_db)):
    """List all sessions."""
    sessions = db.list_sessions()
    return [
        SessionResponse(
            session_id=s.session_id,
            project_path=s.project_path,
            status=s.status,
            created_at=str(s.created_at),
            updated_at=str(s.updated_at),
        )
        for s in sessions
    ]


@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db=Depends(get_db)):
    """Get a single session by ID."""
    session = db.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(
        session_id=session.session_id,
        project_path=session.project_path,
        status=session.status,
        created_at=str(session.created_at),
        updated_at=str(session.updated_at),
    )


@app.get("/api/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(session_id: str, db=Depends(get_db)):
    """Get all messages for a session."""
    # First verify the session exists
    session = db.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = db.get_messages(session_id)
    return [
        MessageResponse(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            timestamp=str(m.timestamp),
        )
        for m in messages
    ]


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            # Echo back for now (can be extended for specific commands)
            await websocket.send_json({"type": "ack", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
