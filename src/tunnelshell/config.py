"""Configuration management for TunnelShell."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os


@dataclass
class SSHConfig:
    """SSH connection configuration."""
    
    host: str
    port: int = 22
    user: Optional[str] = None
    key_filename: Optional[str] = None
    timeout: int = 30
    
    # Connection options
    connect_timeout: int = 10
    banner_timeout: int = 15
    auth_timeout: int = 30
    
    # Keep-alive options
    keepalive_interval: int = 15
    keepalive_count_max: int = 3
    
    @classmethod
    def from_host_alias(cls, host: str, timeout: int = 30) -> "SSHConfig":
        """Create config from host alias or hostname.
        
        Supports:
        - SSH config aliases (reads ~/.ssh/config)
        - Direct hostnames (user@host:port format)
        - IP addresses
        """
        # Parse user@host:port format
        user = None
        port = 22
        
        if "@" in host:
            user, host_part = host.split("@", 1)
        else:
            host_part = host
            
        if ":" in host_part:
            host_str, port_str = host_part.rsplit(":", 1)
            try:
                port = int(port_str)
                host = host_str
            except ValueError:
                pass
        else:
            host = host_part
            
        # Try to read SSH config for more details
        ssh_config_path = Path.home() / ".ssh" / "config"
        if ssh_config_path.exists():
            config_data = cls._parse_ssh_config(ssh_config_path, host)
            if config_data:
                user = user or config_data.get("user")
                port = config_data.get("port", port)
                key_filename = config_data.get("identityfile")
                return cls(
                    host=config_data.get("hostname", host),
                    port=port,
                    user=user,
                    key_filename=key_filename,
                    timeout=timeout,
                )
        
        return cls(host=host, port=port, user=user, timeout=timeout)
    
    @staticmethod
    def _parse_ssh_config(config_path: Path, host_alias: str) -> Optional[dict]:
        """Parse SSH config file for a specific host."""
        try:
            content = config_path.read_text()
        except Exception:
            return None
            
        result = {}
        in_match = False
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
                
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
                
            key, value = parts[0].lower(), parts[1]
            
            if key == "host":
                hosts = value.split()
                in_match = host_alias in hosts or "*" in hosts
                continue
                
            if in_match:
                if key == "hostname":
                    result["hostname"] = value
                elif key == "user":
                    result["user"] = value
                elif key == "port":
                    result["port"] = int(value)
                elif key == "identityfile":
                    result["identityfile"] = os.path.expanduser(value)
                    
        return result if result else None