"""Interactive terminal support for TunnelShell.

Provides real interactive terminal for commands like vim, top, python REPL.
"""

import os
import pty
import select
import signal
import subprocess
import termios
import time
from dataclasses import dataclass, field
from typing import Optional, Tuple
from enum import Enum


class TerminalState(Enum):
    """Terminal state."""
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    KILLED = "killed"


@dataclass
class InteractiveTerminal:
    """Interactive terminal for SSH sessions.

    Allows real interactive terminal sessions (vim, top, etc.)
    instead of just command execution.
    """

    host: str
    command: Optional[str] = None
    rows: int = 24
    cols: int = 80

    _pid: Optional[int] = None
    _fd: Optional[int] = None
    _state: TerminalState = TerminalState.CREATED
    _output_buffer: bytearray = field(default_factory=bytearray)

    @property
    def is_running(self) -> bool:
        """Check if terminal is running."""
        return self._state == TerminalState.RUNNING and self._pid is not None

    def spawn(self, command: Optional[str] = None) -> None:
        """Spawn interactive terminal process.

        Args:
            command: Command to run (default: ssh to host)
        """
        if self.is_running:
            return

        cmd = command or self.command or f"ssh {self.host}"

        # Create PTY
        self._pid, self._fd = pty.fork()

        if self._pid == 0:
            # Child process
            os.setsid()

            # Set terminal size
            winsize = termios.struct_winsize(self.rows, self.cols, 0, 0)
            termios.ioctl(self._fd, termios.TIOCSWINSZ, winsize)

            # Execute command
            os.execvp("ssh", ["ssh", self.host])
        else:
            # Parent process
            self._state = TerminalState.RUNNING

    def send(self, data: str) -> None:
        """Send data to terminal.

        Args:
            data: String to send (can include special keys)
        """
        if not self.is_running:
            raise RuntimeError("Terminal not running")

        # Convert special keys
        if data == "ENTER":
            data = "\n"
        elif data == "ESC":
            data = "\x1b"
        elif data == "CTRL_C":
            data = "\x03"
        elif data == "CTRL_D":
            data = "\x04"

        os.write(self._fd, data.encode())

    def read(self, timeout: float = 0.1) -> str:
        """Read output from terminal.

        Args:
            timeout: Read timeout in seconds

        Returns:
            Output string (may be empty if no data)
        """
        if not self.is_running:
            return ""

        output = ""

        try:
            # Use select to check for data
            ready, _, _ = select.select([self._fd], [], [], timeout)

            if ready:
                data = os.read(self._fd, 4096)
                self._output_buffer.extend(data)
                output = data.decode("utf-8", errors="replace")
        except OSError:
            pass

        return output

    def resize(self, rows: int, cols: int) -> None:
        """Resize terminal window.

        Args:
            rows: New row count
            cols: New column count
        """
        if not self.is_running:
            return

        self.rows = rows
        self.cols = cols

        winsize = termios.struct_winsize(rows, cols, 0, 0)
        termios.ioctl(self._fd, termios.TIOCSWINSZ, winsize)

    def kill(self) -> None:
        """Kill terminal process."""
        if self._pid:
            try:
                os.kill(self._pid, signal.SIGTERM)
                time.sleep(0.1)
                os.kill(self._pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

        if self._fd:
            try:
                os.close(self._fd)
            except OSError:
                pass

        self._pid = None
        self._fd = None
        self._state = TerminalState.KILLED

    def wait(self, timeout: Optional[float] = None) -> int:
        """Wait for terminal process to exit.

        Args:
            timeout: Wait timeout (None = wait forever)

        Returns:
            Exit code of process
        """
        if not self._pid:
            return -1

        try:
            _, status = os.waitpid(self._pid, 0)
            self._state = TerminalState.STOPPED
            return status >> 8
        except ChildProcessError:
            return -1

    def get_output(self) -> str:
        """Get all buffered output.

        Returns:
            All output captured so far
        """
        return self._output_buffer.decode("utf-8", errors="replace")


def create_interactive_session(host: str, command: Optional[str] = None) -> InteractiveTerminal:
    """Create an interactive terminal session.

    Args:
        host: SSH host alias
        command: Optional command to run

    Returns:
        InteractiveTerminal instance
    """
    terminal = InteractiveTerminal(host=host, command=command)
    terminal.spawn()
    return terminal