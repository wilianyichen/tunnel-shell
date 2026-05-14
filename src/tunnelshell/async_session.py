"""Async PTY session management for TunnelShell."""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from enum import Enum

from .async_connection import AsyncConnection, AsyncSSHConfig
from .exceptions import SessionError, SessionNotFoundError, SessionTimeoutError


class AsyncSessionStatus(Enum):
    """Session status."""
    CREATED = "created"
    RUNNING = "running"
    DETACHED = "detached"
    KILLED = "killed"


@dataclass
class AsyncPTYSession:
    """Async PTY session for interactive remote terminal."""
    
    session_id: str
    config: AsyncSSHConfig
    name: Optional[str] = None
    
    _connection: Optional[AsyncConnection] = None
    _process: Optional[asyncio.subprocess.Process] = None
    _status: AsyncSessionStatus = AsyncSessionStatus.CREATED
    _output_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    _output_buffer: List[str] = field(default_factory=list)
    _created_at: float = field(default_factory=time.time)
    
    @property
    def status(self) -> AsyncSessionStatus:
        return self._status
    
    @property
    def is_running(self) -> bool:
        return self._status == AsyncSessionStatus.RUNNING
    
    async def create(self) -> None:
        """Create the PTY session."""
        if self._status != AsyncSessionStatus.CREATED:
            raise SessionError(f"Session {self.session_id} already created")
        
        self._connection = AsyncConnection(self.config)
        await self._connection.connect()
        self._status = AsyncSessionStatus.RUNNING
    
    async def send_line(self, line: str) -> None:
        """Send a line to the session."""
        if not self.is_running:
            raise SessionError(f"Session {self.session_id} is not running")
        
        # Execute command through connection
        await self._connection.execute(line)
    
    async def read_output(self, timeout: float = 1.0) -> str:
        """Read output from the session."""
        if not self.is_running:
            raise SessionError(f"Session {self.session_id} is not running")
        
        try:
            output = await asyncio.wait_for(
                self._output_queue.get(),
                timeout=timeout
            )
            self._output_buffer.append(output)
            return output
        except asyncio.TimeoutError:
            return ""
    
    async def detach(self) -> None:
        """Detach from session (keep running)."""
        if self._status != AsyncSessionStatus.RUNNING:
            return
        
        self._status = AsyncSessionStatus.DETACHED
    
    async def attach(self) -> None:
        """Re-attach to session."""
        if self._status == AsyncSessionStatus.DETACHED:
            self._status = AsyncSessionStatus.RUNNING
        elif self._status == AsyncSessionStatus.CREATED:
            await self.create()
    
    async def kill(self) -> None:
        """Kill the session."""
        if self._connection:
            await self._connection.disconnect()
        
        self._status = AsyncSessionStatus.KILLED
        self._connection = None
    
    def get_info(self) -> dict:
        """Get session info."""
        return {
            "session_id": self.session_id,
            "name": self.name,
            "status": self._status.value,
            "created_at": self._created_at,
            "output_lines": len(self._output_buffer),
        }


class AsyncSessionManager:
    """Manage multiple async PTY sessions."""
    
    def __init__(self):
        self._sessions: Dict[str, AsyncPTYSession] = {}
    
    async def create_session(
        self,
        config: AsyncSSHConfig,
        name: Optional[str] = None
    ) -> AsyncPTYSession:
        """Create a new async session."""
        session_id = f"session_{int(time.time() * 1000)}"
        
        session = AsyncPTYSession(
            session_id=session_id,
            config=config,
            name=name
        )
        
        await session.create()
        self._sessions[session_id] = session
        
        return session
    
    def get_session(self, session_id: str) -> AsyncPTYSession:
        """Get a session by ID."""
        session = self._sessions.get(session_id)
        if not session:
            raise SessionNotFoundError(session_id)
        return session
    
    def list_sessions(self) -> List[dict]:
        """List all sessions."""
        return [s.get_info() for s in self._sessions.values()]
    
    async def kill_session(self, session_id: str) -> None:
        """Kill a session."""
        session = self.get_session(session_id)
        await session.kill()
        del self._sessions[session_id]
    
    async def kill_all(self) -> None:
        """Kill all sessions."""
        for session_id in list(self._sessions.keys()):
            await self.kill_session(session_id)