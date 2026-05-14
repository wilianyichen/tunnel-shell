"""SSH connection management for TunnelShell."""

import socket
import time
from typing import Optional

import paramiko
from paramiko import SSHClient, AutoAddPolicy

from .config import SSHConfig


class ConnectionError(Exception):
    """SSH connection error."""
    pass


class CommandError(Exception):
    """Command execution error."""
    pass


class Connection:
    """SSH connection wrapper with retry and keep-alive support."""
    
    def __init__(self, config: SSHConfig):
        self.config = config
        self._client: Optional[SSHClient] = None
        self._connected = False
        self._last_activity = 0.0
        
    @property
    def is_connected(self) -> bool:
        """Check if connection is active."""
        if not self._client or not self._connected:
            return False
        transport = self._client.get_transport()
        return transport is not None and transport.is_active()
    
    def connect(self) -> None:
        """Establish SSH connection."""
        if self.is_connected:
            return
            
        self._client = SSHClient()
        self._client.set_missing_host_key_policy(AutoAddPolicy())
        
        kwargs = {
            "hostname": self.config.host,
            "port": self.config.port,
            "timeout": self.config.connect_timeout,
            "banner_timeout": self.config.banner_timeout,
            "auth_timeout": self.config.auth_timeout,
        }
        
        if self.config.user:
            kwargs["username"] = self.config.user
            
        if self.config.key_filename:
            kwargs["key_filename"] = self.config.key_filename
            
        try:
            self._client.connect(**kwargs)
            self._connected = True
            self._last_activity = time.time()
            
            transport = self._client.get_transport()
            if transport:
                transport.set_keepalive(self.config.keepalive_interval)
                
        except paramiko.AuthenticationException as e:
            raise ConnectionError(f"Authentication failed: {e}") from e
        except paramiko.SSHException as e:
            raise ConnectionError(f"SSH error: {e}") from e
        except socket.timeout as e:
            raise ConnectionError(f"Connection timeout: {e}") from e
        except socket.error as e:
            raise ConnectionError(f"Socket error: {e}") from e
            
    def disconnect(self) -> None:
        """Close SSH connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._connected = False
            
    def execute(
        self, 
        command: str, 
        timeout: Optional[int] = None,
        environment: Optional[dict] = None,
    ) -> tuple[int, str, str]:
        """Execute a command and return (exit_code, stdout, stderr)."""
        if not self.is_connected:
            self.connect()
            
        timeout = timeout or self.config.timeout
        
        if environment:
            env_str = " ".join(f"{k}={v}" for k, v in environment.items())
            command = f"export {env_str} && {command}"
            
        try:
            stdin, stdout, stderr = self._client.exec_command(command, timeout=timeout)
            stdout_text = stdout.read().decode("utf-8", errors="replace")
            stderr_text = stderr.read().decode("utf-8", errors="replace")
            exit_code = stdout.channel.recv_exit_status()
            
            self._last_activity = time.time()
            return exit_code, stdout_text, stderr_text
            
        except paramiko.SSHException as e:
            raise CommandError(f"Command execution failed: {e}") from e
        except socket.timeout as e:
            raise CommandError(f"Command timeout: {e}") from e
            
    def __enter__(self) -> "Connection":
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()
        
    def __del__(self) -> None:
        self.disconnect()