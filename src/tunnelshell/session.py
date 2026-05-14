"""PTY session management for TunnelShell."""

import enum
import time
import threading
import queue
from dataclasses import dataclass, field
from typing import Optional

from .config import SSHConfig
from .connection import Connection
from .output_buffer import OutputBuffer


class SessionStatus(enum.Enum):
    """Session status."""
    CREATED = "created"
    CONNECTING = "connecting"
    RUNNING = "running"
    DETACHED = "detached"
    COMPLETED = "completed"
    KILLED = "killed"
    ERROR = "error"


@dataclass
class SessionInfo:
    """Session information."""
    session_id: str
    name: Optional[str]
    host: str
    status: SessionStatus
    created_at: float
    cwd: str = ""
    last_output: str = ""
    exit_code: Optional[int] = None


@dataclass
class PTYSession:
    """PTY session for interactive remote terminal."""
    
    session_id: str
    config: SSHConfig
    name: Optional[str] = None
    
    _connection: Optional[Connection] = None
    _channel: Optional[object] = None
    _status: SessionStatus = SessionStatus.CREATED
    _output_queue: queue.Queue = field(default_factory=queue.Queue)
    _output_thread: Optional[threading.Thread] = None
    _stop_event: threading.Event = field(default_factory=threading.Event)
    _output_buffer: OutputBuffer = field(default_factory=OutputBuffer)
    
    created_at: float = field(default_factory=time.time)
    cwd: str = ""
    last_output: str = ""
    
    @property
    def status(self) -> SessionStatus:
        return self._status
        
    def attach(self, rows: int = 24, cols: int = 80) -> None:
        """Attach to the PTY session."""
        if self._status == SessionStatus.RUNNING:
            return
            
        self._status = SessionStatus.CONNECTING
        
        try:
            self._connection = Connection(self.config)
            self._connection.connect()
            
            transport = self._connection._client.get_transport()
            if not transport:
                raise RuntimeError("No transport available")
                
            self._channel = transport.open_session()
            self._channel.get_pty(term="xterm-256color", width=cols, height=rows)
            self._channel.invoke_shell()
            
            self._stop_event.clear()
            self._output_thread = threading.Thread(target=self._read_output, daemon=True)
            self._output_thread.start()
            
            self._status = SessionStatus.RUNNING
            
        except Exception as e:
            self._status = SessionStatus.ERROR
            raise RuntimeError(f"Failed to attach: {e}") from e
            
    def _read_output(self) -> None:
        """Read output from PTY in background thread."""
        while not self._stop_event.is_set() and self._channel:
            try:
                if self._channel.recv_ready():
                    data = self._channel.recv(4096)
                    if data:
                        text = data.decode("utf-8", errors="replace")
                        self._output_queue.put(text)
                        self._output_buffer.append(text)
                        self.last_output = text
                else:
                    time.sleep(0.01)
            except Exception:
                break
                
    def send_line(self, command: str) -> None:
        """Send a command line (with newline)."""
        self.send_text(command + "\n")
        
    def send_text(self, text: str) -> None:
        """Send raw text to PTY."""
        if not self._channel or self._status != SessionStatus.RUNNING:
            raise RuntimeError("Session not running")
        self._channel.send(text.encode("utf-8"))
        
    def send_control(self, control: str) -> None:
        """Send control character."""
        if not self._channel or self._status != SessionStatus.RUNNING:
            raise RuntimeError("Session not running")
            
        control_chars = {
            "c": "\x03",  # Ctrl+C
            "d": "\x04",  # Ctrl+D
            "z": "\x1a",  # Ctrl+Z
            "l": "\x0c",  # Ctrl+L
        }
        
        if control not in control_chars:
            raise ValueError(f"Unknown control: {control}")
            
        self._channel.send(control_chars[control].encode("utf-8"))
        
    def read_output(self, timeout: float = 0.1) -> str:
        """Read available output from PTY."""
        output = []
        try:
            while True:
                text = self._output_queue.get(timeout=timeout)
                output.append(text)
        except queue.Empty:
            pass
        return "".join(output)
        
    def snapshot(self, lines: int = 50) -> str:
        """Get current terminal snapshot."""
        return self.read_output(timeout=0.1)
        
    def get_buffer(self, lines: int = 50, strip_ansi: bool = False) -> str:
        """Get buffered output."""
        output = self._output_buffer.get_recent(lines)
        if strip_ansi:
            output = OutputBuffer.strip_ansi(output)
        return output
        
    def detect_prompt(self) -> Optional[str]:
        """Detect if current output contains an interactive prompt."""
        return OutputBuffer.detect_prompt(self.last_output)
        
    def get_buffer_stats(self) -> dict:
        """Get output buffer statistics."""
        return self._output_buffer.get_stats()
        
    def detach(self) -> None:
        """Detach from session."""
        if self._status == SessionStatus.RUNNING:
            self._status = SessionStatus.DETACHED
            
    def kill(self) -> None:
        """Kill the session."""
        self._stop_event.set()
        
        if self._channel:
            try:
                self._channel.close()
            except Exception:
                pass
            self._channel = None
            
        if self._connection:
            self._connection.disconnect()
            self._connection = None
            
        if self._output_thread and self._output_thread.is_alive():
            self._output_thread.join(timeout=1.0)
            
        self._status = SessionStatus.KILLED
        
    def get_info(self) -> SessionInfo:
        """Get session info."""
        return SessionInfo(
            session_id=self.session_id,
            name=self.name,
            host=self.config.host,
            status=self._status,
            created_at=self.created_at,
            cwd=self.cwd,
            last_output=self.last_output[:200] if self.last_output else "",
        )