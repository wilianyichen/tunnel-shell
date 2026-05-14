"""SSH connection pool for TunnelShell.

Provides connection reuse and management for improved performance.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from contextlib import asynccontextmanager

from .config import SSHConfig
from .async_connection import AsyncConnection, AsyncSSHConfig
from .exceptions import ConnectionError


@dataclass
class PooledConnection:
    """A pooled connection with metadata."""
    
    connection: AsyncConnection
    config: SSHConfig
    created_at: float
    last_used: float
    in_use: bool = False
    
    def is_expired(self, max_age: float = 3600) -> bool:
        """Check if connection is expired."""
        return time.time() - self.created_at > max_age
    
    def is_idle_too_long(self, max_idle: float = 300) -> bool:
        """Check if connection has been idle too long."""
        return not self.in_use and time.time() - self.last_used > max_idle


class ConnectionPool:
    """SSH connection pool for connection reuse."""
    
    def __init__(
        self,
        max_connections: int = 10,
        max_age: float = 3600,
        max_idle: float = 300,
    ):
        """
        Initialize connection pool.
        
        Args:
            max_connections: Maximum number of connections per host
            max_age: Maximum age of a connection in seconds
            max_idle: Maximum idle time before cleanup
        """
        self.max_connections = max_connections
        self.max_age = max_age
        self.max_idle = max_idle
        
        self._pool: Dict[str, List[PooledConnection]] = {}
        self._lock = asyncio.Lock()
    
    def _get_host_key(self, config: SSHConfig) -> str:
        """Get unique key for a host configuration."""
        return f"{config.user}@{config.host}:{config.port}"
    
    async def get(self, config: SSHConfig) -> AsyncConnection:
        """
        Get a connection from the pool.
        
        Returns an existing idle connection or creates a new one.
        """
        host_key = self._get_host_key(config)
        
        async with self._lock:
            # Initialize pool for this host if needed
            if host_key not in self._pool:
                self._pool[host_key] = []
            
            # Clean up expired/idle connections
            await self._cleanup_host(host_key)
            
            # Find an available connection
            for pooled in self._pool[host_key]:
                if not pooled.in_use and pooled.connection.is_connected:
                    pooled.in_use = True
                    pooled.last_used = time.time()
                    return pooled.connection
            
            # Create new connection if under limit
            if len(self._pool[host_key]) < self.max_connections:
                connection = await self._create_connection(config)
                pooled = PooledConnection(
                    connection=connection,
                    config=config,
                    created_at=time.time(),
                    last_used=time.time(),
                    in_use=True,
                )
                self._pool[host_key].append(pooled)
                return connection
            
            # Pool is full, wait for a connection
            raise ConnectionError(
                f"Connection pool for {host_key} is full. "
                f"Max connections: {self.max_connections}"
            )
    
    async def release(self, config: SSHConfig, connection: AsyncConnection) -> None:
        """Release a connection back to the pool."""
        host_key = self._get_host_key(config)
        
        async with self._lock:
            if host_key in self._pool:
                for pooled in self._pool[host_key]:
                    if pooled.connection is connection:
                        pooled.in_use = False
                        pooled.last_used = time.time()
                        break
    
    async def _create_connection(self, config: SSHConfig) -> AsyncConnection:
        """Create a new async connection."""
        async_config = AsyncSSHConfig(config)
        connection = AsyncConnection(async_config)
        await connection.connect()
        return connection
    
    async def _cleanup_host(self, host_key: str) -> None:
        """Clean up expired/idle connections for a host."""
        if host_key not in self._pool:
            return
        
        to_remove = []
        
        for pooled in self._pool[host_key]:
            # Remove expired connections
            if pooled.is_expired(self.max_age):
                to_remove.append(pooled)
                continue
            
            # Remove idle connections
            if pooled.is_idle_too_long(self.max_idle):
                to_remove.append(pooled)
                continue
            
            # Remove disconnected connections
            if not pooled.connection.is_connected:
                to_remove.append(pooled)
        
        for pooled in to_remove:
            try:
                await pooled.connection.disconnect()
            except Exception:
                pass
            self._pool[host_key].remove(pooled)
    
    async def cleanup(self) -> None:
        """Clean up all expired/idle connections."""
        async with self._lock:
            for host_key in list(self._pool.keys()):
                await self._cleanup_host(host_key)
                
                # Remove empty host entries
                if not self._pool[host_key]:
                    del self._pool[host_key]
    
    async def close_all(self) -> None:
        """Close all connections in the pool."""
        async with self._lock:
            for host_key in list(self._pool.keys()):
                for pooled in self._pool[host_key]:
                    try:
                        await pooled.connection.disconnect()
                    except Exception:
                        pass
                del self._pool[host_key]
    
    @asynccontextmanager
    async def connection(self, config: SSHConfig):
        """
        Context manager for getting and releasing connections.
        
        Usage:
            async with pool.connection(config) as conn:
                await conn.execute("ls")
        """
        connection = await self.get(config)
        try:
            yield connection
        finally:
            await self.release(config, connection)
    
    def get_stats(self) -> dict:
        """Get pool statistics."""
        stats = {
            "hosts": len(self._pool),
            "total_connections": sum(len(conns) for conns in self._pool.values()),
            "active_connections": sum(
                sum(1 for p in conns if p.in_use)
                for conns in self._pool.values()
            ),
            "idle_connections": sum(
                sum(1 for p in conns if not p.in_use)
                for conns in self._pool.values()
            ),
        }
        return stats


# Global connection pool instance
_global_pool: Optional[ConnectionPool] = None


def get_pool() -> ConnectionPool:
    """Get the global connection pool."""
    global _global_pool
    if _global_pool is None:
        _global_pool = ConnectionPool()
    return _global_pool


async def close_global_pool() -> None:
    """Close the global connection pool."""
    global _global_pool
    if _global_pool is not None:
        await _global_pool.close_all()
        _global_pool = None
