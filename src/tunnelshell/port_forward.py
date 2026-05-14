"""Port forwarding for TunnelShell.

Supports local and remote port forwarding via SSH.
"""

import socket
import threading
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Callable
from enum import Enum
import paramiko


class ForwardType(Enum):
    """Port forward type."""
    LOCAL = "local"      # Local port -> Remote host
    REMOTE = "remote"    # Remote port -> Local host
    DYNAMIC = "dynamic"  # SOCKS proxy


@dataclass
class PortForward:
    """Port forward configuration."""

    forward_type: ForwardType
    local_host: str
    local_port: int
    remote_host: str
    remote_port: int

    _thread: Optional[threading.Thread] = None
    _running: bool = False
    _transport: Optional[paramiko.Transport] = None


class ForwardManager:
    """Manage multiple port forwards."""

    def __init__(self, transport: paramiko.Transport):
        """
        Initialize forward manager.

        Args:
            transport: SSH transport from paramiko connection
        """
        self._transport = transport
        self._forwards: Dict[str, PortForward] = {}
        self._lock = threading.Lock()

    def add_local_forward(
        self,
        local_port: int,
        remote_host: str,
        remote_port: int,
        name: Optional[str] = None,
        local_host: str = "127.0.0.1"
    ) -> str:
        """
        Add local port forward.

        Local port -> Remote host:port

        Args:
            local_port: Local port to listen on
            remote_host: Remote host to forward to
            remote_port: Remote port to forward to
            name: Forward name (auto-generated if None)
            local_host: Local host to bind (default: 127.0.0.1)

        Returns:
            Forward ID
        """
        forward_id = name or f"local_{local_port}_{remote_host}_{remote_port}"

        forward = PortForward(
            forward_type=ForwardType.LOCAL,
            local_host=local_host,
            local_port=local_port,
            remote_host=remote_host,
            remote_port=remote_port
        )

        with self._lock:
            self._forwards[forward_id] = forward

        return forward_id

    def add_remote_forward(
        self,
        remote_port: int,
        local_host: str,
        local_port: int,
        name: Optional[str] = None,
        remote_host: str = "127.0.0.1"
    ) -> str:
        """
        Add remote port forward.

        Remote port -> Local host:port

        Args:
            remote_port: Remote port to listen on
            local_host: Local host to forward to
            local_port: Local port to forward to
            name: Forward name (auto-generated if None)
            remote_host: Remote host to bind (default: 127.0.0.1)

        Returns:
            Forward ID
        """
        forward_id = name or f"remote_{remote_port}_{local_host}_{local_port}"

        forward = PortForward(
            forward_type=ForwardType.REMOTE,
            local_host=local_host,
            local_port=local_port,
            remote_host=remote_host,
            remote_port=remote_port
        )

        with self._lock:
            self._forwards[forward_id] = forward

        return forward_id

    def start_forward(self, forward_id: str) -> bool:
        """
        Start a port forward.

        Args:
            forward_id: Forward ID

        Returns:
            True if started successfully
        """
        with self._lock:
            forward = self._forwards.get(forward_id)
            if not forward:
                return False

            if forward._running:
                return True

            forward._transport = self._transport

            if forward.forward_type == ForwardType.LOCAL:
                forward._thread = threading.Thread(
                    target=self._run_local_forward,
                    args=(forward),
                    daemon=True
                )
            else:
                forward._thread = threading.Thread(
                    target=self._run_remote_forward,
                    args=(forward),
                    daemon=True
                )

            forward._running = True
            forward._thread.start()

        return True

    def stop_forward(self, forward_id: str) -> bool:
        """
        Stop a port forward.

        Args:
            forward_id: Forward ID

        Returns:
            True if stopped successfully
        """
        with self._lock:
            forward = self._forwards.get(forward_id)
            if not forward:
                return False

            forward._running = False

            if forward_id in self._forwards:
                del self._forwards[forward_id]

        return True

    def list_forwards(self) -> list:
        """
        List all port forwards.

        Returns:
            List of forward info dicts
        """
        with self._lock:
            return [
                {
                    "id": fid,
                    "type": f.forward_type.value,
                    "local": f"{f.local_host}:{f.local_port}",
                    "remote": f"{f.remote_host}:{f.remote_port}",
                    "running": f._running
                }
                for fid, f in self._forwards.items()
            ]

    def stop_all(self) -> None:
        """Stop all port forwards."""
        with self._lock:
            for forward in self._forwards.values():
                forward._running = False
            self._forwards.clear()

    def _run_local_forward(self, forward: PortForward) -> None:
        """Run local port forward thread."""
        try:
            # Create local socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((forward.local_host, forward.local_port))
            sock.listen(5)

            while forward._running:
                sock.settimeout(1.0)
                try:
                    client, addr = sock.accept()
                    chan = self._transport.open_channel(
                        "direct-tcpip",
                        (forward.remote_host, forward.remote_port),
                        addr
                    )

                    if chan:
                        # Forward data between client and channel
                        threading.Thread(
                            target=self._forward_data,
                            args=(client, chan),
                            daemon=True
                        ).start()
                except socket.timeout:
                    continue
                except Exception:
                    break

            sock.close()
        except Exception:
            forward._running = False

    def _run_remote_forward(self, forward: PortForward) -> None:
        """Run remote port forward thread."""
        try:
            # Request remote port forward from SSH server
            self._transport.request_port_forward(
                forward.remote_host,
                forward.remote_port
            )

            while forward._running:
                chan = self._transport.accept(1.0)
                if chan:
                    # Connect to local target
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((forward.local_host, forward.local_port))

                    # Forward data
                    threading.Thread(
                        target=self._forward_data,
                        args=(chan, sock),
                        daemon=True
                    ).start()
        except Exception:
            forward._running = False

    def _forward_data(self, source: socket.socket, dest: socket.socket) -> None:
        """Forward data between two sockets."""
        try:
            while True:
                data = source.recv(4096)
                if not data:
                    break
                dest.send(data)
        except Exception:
            pass
        finally:
            try:
                source.close()
            except Exception:
                pass
            try:
                dest.close()
            except Exception:
                pass


def create_forward_manager(transport: paramiko.Transport) -> ForwardManager:
    """Create a forward manager.

    Args:
        transport: SSH transport

    Returns:
        ForwardManager instance
    """
    return ForwardManager(transport)