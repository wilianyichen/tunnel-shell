"""Session store for managing multiple PTY sessions with file persistence."""

import uuid
import json
import time
from pathlib import Path
from typing import Dict, Optional, List
import fcntl

from .session import PTYSession, SessionInfo, SessionStatus
from .config import SSHConfig


class SessionStore:
    """Manages multiple PTY sessions with file persistence."""
    
    def __init__(self, state_dir: Optional[Path] = None):
        self._sessions: Dict[str, PTYSession] = {}
        self._state_dir = state_dir or Path.home() / ".tunnelshell" / "sessions"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._metadata_file = self._state_dir / "sessions.json"
        
        # Load persisted session metadata
        self._load_metadata()
        
    def _load_metadata(self) -> None:
        """Load session metadata from file."""
        if not self._metadata_file.exists():
            return
            
        try:
            with open(self._metadata_file, "r") as f:
                data = json.load(f)
                
            for session_data in data.get("sessions", []):
                if session_data.get("status") not in ("killed", "completed", "error"):
                    self._sessions[session_data["session_id"]] = {
                        "session_id": session_data["session_id"],
                        "name": session_data.get("name"),
                        "host": session_data.get("host"),
                        "config_data": session_data.get("config"),
                        "status": session_data.get("status", "detached"),
                    }
        except Exception:
            pass
            
    def _save_metadata(self) -> None:
        """Save session metadata to file with file locking."""
        sessions_data = []
        
        for session_id, session in self._sessions.items():
            if isinstance(session, PTYSession):
                info = session.get_info()
                sessions_data.append({
                    "session_id": info.session_id,
                    "name": info.name,
                    "host": info.host,
                    "status": info.status.value,
                    "config": {
                        "host": session.config.host,
                        "port": session.config.port,
                        "user": session.config.user,
                        "key_filename": session.config.key_filename,
                    },
                })
            elif isinstance(session, dict):
                sessions_data.append({
                    "session_id": session["session_id"],
                    "name": session.get("name"),
                    "host": session.get("host"),
                    "status": session.get("status", "detached"),
                    "config": session.get("config_data"),
                })
                
        # Write with file lock
        with open(self._metadata_file, "w") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump({
                    "sessions": sessions_data,
                    "updated_at": time.time(),
                }, f, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        
    def create(self, config: SSHConfig, name: Optional[str] = None) -> PTYSession:
        """Create a new session."""
        session_id = self._generate_id()
        
        session = PTYSession(
            session_id=session_id,
            config=config,
            name=name,
        )
        
        self._sessions[session_id] = session
        self._save_metadata()
        return session
        
    def get(self, session_id: str) -> Optional[PTYSession]:
        """Get a session by ID."""
        session = self._sessions.get(session_id)
        if isinstance(session, dict):
            return self._reconstruct_session(session)
        return session
        
    def get_by_name(self, name: str) -> Optional[PTYSession]:
        """Get a session by name."""
        for session in self._sessions.values():
            session_name = session.name if isinstance(session, PTYSession) else session.get("name")
            if session_name == name:
                if isinstance(session, dict):
                    return self._reconstruct_session(session)
                return session
        return None
        
    def _reconstruct_session(self, data: dict) -> PTYSession:
        """Reconstruct a PTYSession from stored metadata."""
        config_data = data.get("config_data", {})
        config = SSHConfig(
            host=config_data.get("host", "localhost"),
            port=config_data.get("port", 22),
            user=config_data.get("user"),
            key_filename=config_data.get("key_filename"),
        )
        return PTYSession(
            session_id=data["session_id"],
            config=config,
            name=data.get("name"),
        )
        
    def list(self) -> List[SessionInfo]:
        """List all sessions."""
        result = []
        for session in self._sessions.values():
            if isinstance(session, PTYSession):
                result.append(session.get_info())
            elif isinstance(session, dict):
                status = SessionStatus.DETACHED
                if session.get("status") == "created":
                    status = SessionStatus.CREATED
                result.append(SessionInfo(
                    session_id=session["session_id"],
                    name=session.get("name"),
                    host=session.get("host", ""),
                    status=status,
                    created_at=time.time(),
                ))
        return result
        
    def kill(self, session_id: str) -> bool:
        """Kill a session."""
        session = self._sessions.get(session_id)
        if session:
            if isinstance(session, PTYSession):
                session.kill()
            del self._sessions[session_id]
            self._save_metadata()
            return True
        return False
        
    def kill_by_name(self, name: str) -> bool:
        """Kill a session by name."""
        session = self.get_by_name(name)
        if session:
            return self.kill(session.session_id)
        return False
        
    def update_status(self, session_id: str, status: SessionStatus) -> None:
        """Update session status and persist."""
        session = self._sessions.get(session_id)
        if session and isinstance(session, PTYSession):
            session._status = status
            self._save_metadata()
        
    def cleanup(self) -> int:
        """Remove all killed/error sessions."""
        to_remove = [
            sid for sid, session in self._sessions.items()
            if (isinstance(session, PTYSession) and 
                session.status in (SessionStatus.KILLED, SessionStatus.COMPLETED, SessionStatus.ERROR))
        ]
        for sid in to_remove:
            del self._sessions[sid]
        if to_remove:
            self._save_metadata()
        return len(to_remove)
        
    def _generate_id(self) -> str:
        """Generate a unique session ID."""
        return f"session_{uuid.uuid4().hex[:8]}"