"""Asynchronous SSH connection management using asyncssh.

This module provides async versions of the SSH connection functionality,
enabling non-blocking SSH operations for high-concurrency scenarios.
"""

import asyncio
from typing import Optional

import asyncssh

from .config import SSHConfig
from .exceptions import (
    AuthenticationError,
    ConnectionError,
    ConnectionTimeoutError,
    HostKeyError,
    CommandFailedError,
    CommandTimeoutError,
)


class AsyncSSHConfig:
    """Configuration adapter for asyncssh from SSHConfig.
    
    Converts the synchronous SSHConfig to asyncssh-compatible format.
    """
    
    def __init__(self, config: SSHConfig):
        """Initialize from SSHConfig.
        
        Args:
            config: SSHConfig instance to convert
        """
        self._config = config
        
    @property
    def host(self) -> str:
        """Target host."""
        return self._config.host
    
    @property
    def port(self) -> int:
        """SSH port."""
        return self._config.port
    
    @property
    def username(self) -> Optional[str]:
        """SSH username."""
        return self._config.user
    
    @property
    def client_keys(self) -> Optional[list[str]]:
        """SSH private key paths."""
        if self._config.key_filename:
            return [self._config.key_filename]
        return None
    
    @property
    def connect_timeout(self) -> int:
        """Connection timeout in seconds."""
        return self._config.connect_timeout
    
    @property
    def keepalive_interval(self) -> Optional[int]:
        """Keep-alive interval in seconds."""
        return self._config.keepalive_interval
    
    def to_asyncssh_kwargs(self) -> dict:
        """Convert to asyncssh connect() keyword arguments.
        
        Returns:
            Dict of arguments for asyncssh.connect()
        """
        kwargs = {
            "host": self.host,
            "port": self.port,
            "timeout": self.connect_timeout,
        }
        
        if self.username:
            kwargs["username"] = self.username
            
        if self.client_keys:
            kwargs["client_keys"] = self.client_keys
            
        if self.keepalive_interval:
            kwargs["keepalive_interval"] = self.keepalive_interval
            
        return kwargs


class AsyncConnection:
    """Asynchronous SSH connection wrapper using asyncssh.
    
    Provides async methods for connecting, executing commands, and
    disconnecting from SSH servers with proper error handling.
    
    Example:
        async with AsyncConnection(config) as conn:
            exit_code, stdout, stderr = await conn.execute("ls -la")
    """
    
    def __init__(self, config: SSHConfig):
        """Initialize async connection.
        
        Args:
            config: SSH connection configuration
        """
        self._config = config
        self._async_config = AsyncSSHConfig(config)
        self._conn: Optional[asyncssh.SSHClientConnection] = None
        self._connected = False
        
    @property
    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self._conn is not None and self._connected
    
    async def connect(self) -> None:
        """Establish asynchronous SSH connection.
        
        Raises:
            AuthenticationError: If authentication fails
            HostKeyError: If host key verification fails
            ConnectionTimeoutError: If connection times out
            ConnectionError: For other connection failures
        """
        if self.is_connected:
            return
            
        kwargs = self._async_config.to_asyncssh_kwargs()
        
        try:
            self._conn = await asyncio.wait_for(
                asyncssh.connect(**kwargs),
                timeout=self._config.connect_timeout
            )
            self._connected = True
            
        except asyncssh.PermissionDenied as e:
            raise AuthenticationError(f"Authentication failed: {e}") from e
            
        except asyncssh.HostKeyNotVerifiable as e:
            raise HostKeyError(self._config.host) from e
            
        except asyncio.TimeoutError as e:
            raise ConnectionTimeoutError(
                self._config.host, 
                self._config.connect_timeout
            ) from e
            
        except asyncssh.Error as e:
            raise ConnectionError(
                f"SSH connection error: {e}",
                suggestion="Check host accessibility and SSH service status."
            ) from e
            
        except OSError as e:
            raise ConnectionError(
                f"Network error: {e}",
                suggestion="Check network connectivity and firewall settings."
            ) from e
    
    async def execute(
        self,
        command: str,
        timeout: Optional[int] = None,
        environment: Optional[dict] = None,
    ) -> tuple[int, str, str]:
        """Execute a command asynchronously.
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds (uses config default if None)
            environment: Environment variables to set
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
            
        Raises:
            ConnectionError: If not connected
            CommandTimeoutError: If command times out
            CommandFailedError: If command fails (optional, based on usage)
        """
        if not self.is_connected:
            await self.connect()
            
        timeout = timeout or self._config.timeout
        
        if environment:
            env_str = " ".join(f"{k}={v}" for k, v in environment.items())
            command = f"export {env_str} && {command}"
            
        try:
            result = await asyncio.wait_for(
                self._conn.run(command),
                timeout=timeout
            )
            
            return (
                result.exit_status,
                result.stdout,
                result.stderr
            )
            
        except asyncio.TimeoutError as e:
            raise CommandTimeoutError(command, timeout) from e
            
        except asyncssh.Error as e:
            raise ConnectionError(
                f"Command execution failed: {e}",
                suggestion="Check SSH connection and command syntax."
            ) from e
    
    async def disconnect(self) -> None:
        """Close the SSH connection asynchronously."""
        if self._conn:
            self._conn.close()
            await self._conn.wait_closed()
            self._conn = None
            self._connected = False
            
    async def __aenter__(self) -> "AsyncConnection":
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()
        
    def __del__(self) -> None:
        """Cleanup on deletion."""
        if self._conn and self._connected:
            # Best effort close - can't await in __del__
            self._conn.close()
