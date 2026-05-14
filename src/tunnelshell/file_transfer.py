"""File transfer for TunnelShell.

Provides SFTP-based file upload/download functionality.
"""

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable

import paramiko

from .config import SSHConfig
from .connection import Connection


@dataclass
class TransferProgress:
    """File transfer progress information."""
    local_path: str
    remote_path: str
    total_bytes: int
    transferred_bytes: int
    percent: float
    speed: float  # bytes per second
    eta: float    # seconds remaining
    
    @property
    def is_complete(self) -> bool:
        return self.transferred_bytes >= self.total_bytes


class FileTransfer:
    """SFTP-based file transfer."""
    
    def __init__(self, config: SSHConfig):
        self.config = config
        self._sftp: Optional[paramiko.SFTPClient] = None
        self._transport: Optional[paramiko.Transport] = None
        
    def connect(self) -> None:
        """Establish SFTP connection."""
        if self._sftp:
            return
            
        # Create SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        kwargs = {
            "hostname": self.config.host,
            "port": self.config.port,
            "timeout": self.config.connect_timeout,
        }
        
        if self.config.user:
            kwargs["username"] = self.config.user
        if self.config.key_filename:
            kwargs["key_filename"] = self.config.key_filename
            
        client.connect(**kwargs)
        
        self._transport = client.get_transport()
        self._sftp = paramiko.SFTPClient.from_transport(self._transport)
        
    def disconnect(self) -> None:
        """Close SFTP connection."""
        if self._sftp:
            self._sftp.close()
            self._sftp = None
        if self._transport:
            self._transport.close()
            self._transport = None
            
    def upload(
        self,
        local_path: str,
        remote_path: str,
        progress_callback: Optional[Callable[[TransferProgress], None]] = None,
    ) -> TransferProgress:
        """Upload a file to remote server."""
        self.connect()
        
        local_path = os.path.expanduser(local_path)
        total_bytes = os.path.getsize(local_path)
        transferred = 0
        start_time = time.time()
        last_update = start_time
        
        # Create remote directory if needed
        remote_dir = os.path.dirname(remote_path)
        if remote_dir:
            try:
                self._sftp.stat(remote_dir)
            except FileNotFoundError:
                self._mkdir_p(remote_dir)
        
        # Upload with progress tracking
        with open(local_path, 'rb') as local_file:
            with self._sftp.file(remote_path, 'w') as remote_file:
                chunk_size = 32768
                while True:
                    chunk = local_file.read(chunk_size)
                    if not chunk:
                        break
                    
                    remote_file.write(chunk)
                    transferred += len(chunk)
                    
                    # Update progress
                    now = time.time()
                    if now - last_update >= 0.1 or transferred == total_bytes:
                        elapsed = now - start_time
                        speed = transferred / elapsed if elapsed > 0 else 0
                        eta = (total_bytes - transferred) / speed if speed > 0 else 0
                        
                        progress = TransferProgress(
                            local_path=local_path,
                            remote_path=remote_path,
                            total_bytes=total_bytes,
                            transferred_bytes=transferred,
                            percent=transferred / total_bytes * 100 if total_bytes > 0 else 100,
                            speed=speed,
                            eta=eta,
                        )
                        
                        if progress_callback:
                            progress_callback(progress)
                            
                        last_update = now
        
        return progress
        
    def download(
        self,
        remote_path: str,
        local_path: str,
        progress_callback: Optional[Callable[[TransferProgress], None]] = None,
    ) -> TransferProgress:
        """Download a file from remote server."""
        self.connect()
        
        local_path = os.path.expanduser(local_path)
        
        # Get remote file size
        remote_stat = self._sftp.stat(remote_path)
        total_bytes = remote_stat.st_size
        transferred = 0
        start_time = time.time()
        last_update = start_time
        
        # Create local directory if needed
        local_dir = os.path.dirname(local_path)
        if local_dir:
            os.makedirs(local_dir, exist_ok=True)
        
        # Download with progress tracking
        with self._sftp.file(remote_path, 'r') as remote_file:
            with open(local_path, 'wb') as local_file:
                chunk_size = 32768
                while True:
                    chunk = remote_file.read(chunk_size)
                    if not chunk:
                        break
                    
                    local_file.write(chunk)
                    transferred += len(chunk)
                    
                    # Update progress
                    now = time.time()
                    if now - last_update >= 0.1 or transferred == total_bytes:
                        elapsed = now - start_time
                        speed = transferred / elapsed if elapsed > 0 else 0
                        eta = (total_bytes - transferred) / speed if speed > 0 else 0
                        
                        progress = TransferProgress(
                            local_path=local_path,
                            remote_path=remote_path,
                            total_bytes=total_bytes,
                            transferred_bytes=transferred,
                            percent=transferred / total_bytes * 100 if total_bytes > 0 else 100,
                            speed=speed,
                            eta=eta,
                        )
                        
                        if progress_callback:
                            progress_callback(progress)
                            
                        last_update = now
        
        return progress
        
    def _mkdir_p(self, path: str) -> None:
        """Create directory and parents (like mkdir -p)."""
        parts = path.split('/')
        current = ''
        
        for part in parts:
            if not part:
                continue
            current = f"{current}/{part}"
            
            try:
                self._sftp.stat(current)
            except FileNotFoundError:
                self._sftp.mkdir(current)
                
    def list_dir(self, path: str = '.') -> list[str]:
        """List files in remote directory."""
        self.connect()
        return self._sftp.listdir(path)
        
    def stat(self, path: str) -> paramiko.SFTPAttributes:
        """Get file stats."""
        self.connect()
        return self._sftp.stat(path)
        
    def exists(self, path: str) -> bool:
        """Check if file exists on remote."""
        try:
            self.connect()
            self._sftp.stat(path)
            return True
        except FileNotFoundError:
            return False
            
    def delete(self, path: str) -> None:
        """Delete remote file."""
        self.connect()
        self._sftp.remove(path)
        
    def __enter__(self) -> "FileTransfer":
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()