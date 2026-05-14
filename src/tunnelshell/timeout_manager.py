"""Timeout management for TunnelShell.

Provides multi-level timeout control for sessions and commands.
"""

import signal
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable
from contextlib import contextmanager


class TimeoutType(Enum):
    """Type of timeout."""
    SESSION = "session"       # Maximum session duration
    COMMAND = "command"       # Maximum command execution time
    IDLE = "idle"             # Maximum idle time (no output)
    CONNECT = "connect"       # Connection establishment timeout


@dataclass
class TimeoutConfig:
    """Timeout configuration."""
    session_timeout: int = 3600      # 1 hour max session
    command_timeout: int = 300       # 5 minutes max command
    idle_timeout: int = 60           # 60 seconds idle detection
    connect_timeout: int = 30        # 30 seconds to connect
    
    # Grace periods before forceful termination
    command_grace_period: int = 5    # Wait 5s after SIGINT before SIGTERM
    session_grace_period: int = 10   # Wait 10s after SIGTERM before SIGKILL


class TimeoutError(Exception):
    """Timeout exceeded error."""
    timeout_type: TimeoutType
    elapsed: float
    
    def __init__(self, timeout_type: TimeoutType, elapsed: float, message: str = ""):
        self.timeout_type = timeout_type
        self.elapsed = elapsed
        super().__init__(message or f"{timeout_type.value} timeout after {elapsed:.1f}s")


class TimeoutManager:
    """Manages timeouts for sessions and commands."""
    
    def __init__(self, config: TimeoutConfig):
        self.config = config
        self._start_time: Optional[float] = None
        self._last_activity: Optional[float] = None
        self._timers: dict = {}
        
    def start_session(self) -> None:
        """Start session timer."""
        self._start_time = time.time()
        self._last_activity = time.time()
        
    def record_activity(self) -> None:
        """Record activity (output received)."""
        self._last_activity = time.time()
        
    def check_session_timeout(self) -> Optional[TimeoutError]:
        """Check if session timeout exceeded."""
        if not self._start_time:
            return None
            
        elapsed = time.time() - self._start_time
        if elapsed > self.config.session_timeout:
            return TimeoutError(
                TimeoutType.SESSION,
                elapsed,
                f"Session exceeded {self.config.session_timeout}s limit"
            )
        return None
        
    def check_idle_timeout(self) -> Optional[TimeoutError]:
        """Check if idle timeout exceeded."""
        if not self._last_activity:
            return None
            
        idle_time = time.time() - self._last_activity
        if idle_time > self.config.idle_timeout:
            return TimeoutError(
                TimeoutType.IDLE,
                idle_time,
                f"No output for {self.config.idle_timeout}s"
            )
        return None
        
    @contextmanager
    def command_timeout(self, timeout: Optional[int] = None):
        """Context manager for command timeout.
        
        Raises TimeoutError if command exceeds timeout.
        """
        timeout = timeout or self.config.command_timeout
        
        def timeout_handler(signum, frame):
            raise TimeoutError(
                TimeoutType.COMMAND,
                timeout,
                f"Command exceeded {timeout}s limit"
            )
        
        # Set up signal handler (only works in main thread)
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
            
    def get_remaining_time(self, timeout_type: TimeoutType) -> float:
        """Get remaining time for a timeout type."""
        if timeout_type == TimeoutType.SESSION:
            if not self._start_time:
                return self.config.session_timeout
            elapsed = time.time() - self._start_time
            return max(0, self.config.session_timeout - elapsed)
            
        elif timeout_type == TimeoutType.IDLE:
            if not self._last_activity:
                return self.config.idle_timeout
            idle_time = time.time() - self._last_activity
            return max(0, self.config.idle_timeout - idle_time)
            
        return 0
        
    def get_stats(self) -> dict:
        """Get timeout statistics."""
        return {
            "session_elapsed": time.time() - self._start_time if self._start_time else 0,
            "session_remaining": self.get_remaining_time(TimeoutType.SESSION),
            "idle_time": time.time() - self._last_activity if self._last_activity else 0,
            "idle_remaining": self.get_remaining_time(TimeoutType.IDLE),
        }


# Default timeout configuration
DEFAULT_TIMEOUT_CONFIG = TimeoutConfig()


def create_timeout_manager(
    session_timeout: Optional[int] = None,
    command_timeout: Optional[int] = None,
    idle_timeout: Optional[int] = None,
) -> TimeoutManager:
    """Create a timeout manager with custom settings."""
    config = TimeoutConfig(
        session_timeout=session_timeout or DEFAULT_TIMEOUT_CONFIG.session_timeout,
        command_timeout=command_timeout or DEFAULT_TIMEOUT_CONFIG.command_timeout,
        idle_timeout=idle_timeout or DEFAULT_TIMEOUT_CONFIG.idle_timeout,
    )
    return TimeoutManager(config)