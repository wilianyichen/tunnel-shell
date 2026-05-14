"""Configuration management for TunnelShell.

Supports YAML/TOML config files for server profiles and defaults.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, List, Any
import yaml


@dataclass
class ServerProfile:
    """Server profile configuration."""

    name: str
    host: str
    port: int = 22
    user: Optional[str] = None
    key_filename: Optional[str] = None
    timeout: int = 30

    # Tags and capabilities
    tags: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)

    # Environment
    environment: Dict[str, str] = field(default_factory=dict)
    work_dirs: List[str] = field(default_factory=list)

    # Notes
    notes: str = ""

    def to_ssh_config(self) -> Dict[str, Any]:
        """Convert to SSH config format."""
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "key_filename": self.key_filename,
            "timeout": self.timeout
        }


@dataclass
class TunnelShellConfig:
    """TunnelShell configuration."""

    servers: Dict[str, ServerProfile] = field(default_factory=dict)
    defaults: Dict[str, Any] = field(default_factory=dict)
    groups: Dict[str, List[str]] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Optional[str] = None) -> "TunnelShellConfig":
        """
        Load configuration from file.

        Args:
            path: Config file path (default: ~/.tunnelshell/config.yaml)

        Returns:
            TunnelShellConfig instance
        """
        if path is None:
            path = os.path.expanduser("~/.tunnelshell/config.yaml")

        if not os.path.exists(path):
            return cls()

        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}

        config = cls()

        # Load servers
        for name, server_data in data.get("servers", {}).items():
            config.servers[name] = ServerProfile(
                name=name,
                host=server_data.get("host", name),
                port=server_data.get("port", 22),
                user=server_data.get("user"),
                key_filename=server_data.get("key_filename"),
                timeout=server_data.get("timeout", 30),
                tags=server_data.get("tags", []),
                capabilities=server_data.get("capabilities", []),
                environment=server_data.get("environment", {}),
                work_dirs=server_data.get("work_dirs", []),
                notes=server_data.get("notes", "")
            )

        # Load defaults
        config.defaults = data.get("defaults", {
            "timeout": 30,
            "connect_timeout": 10,
            "keepalive_interval": 15
        })

        # Load groups
        config.groups = data.get("groups", {})

        return config

    def save(self, path: Optional[str] = None) -> None:
        """
        Save configuration to file.

        Args:
            path: Config file path (default: ~/.tunnelshell/config.yaml)
        """
        if path is None:
            path = os.path.expanduser("~/.tunnelshell/config.yaml")

        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)

        data = {
            "servers": {
                name: {
                    "host": s.host,
                    "port": s.port,
                    "user": s.user,
                    "key_filename": s.key_filename,
                    "timeout": s.timeout,
                    "tags": s.tags,
                    "capabilities": s.capabilities,
                    "environment": s.environment,
                    "work_dirs": s.work_dirs,
                    "notes": s.notes
                }
                for name, s in self.servers.items()
            },
            "defaults": self.defaults,
            "groups": self.groups
        }

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

    def get_server(self, name: str) -> Optional[ServerProfile]:
        """
        Get server profile by name.

        Args:
            name: Server name

        Returns:
            ServerProfile or None if not found
        """
        return self.servers.get(name)

    def list_servers(self) -> List[str]:
        """
        List all server names.

        Returns:
            List of server names
        """
        return list(self.servers.keys())

    def add_server(self, profile: ServerProfile) -> None:
        """
        Add a server profile.

        Args:
            profile: ServerProfile to add
        """
        self.servers[profile.name] = profile

    def remove_server(self, name: str) -> bool:
        """
        Remove a server profile.

        Args:
            name: Server name

        Returns:
            True if removed, False if not found
        """
        if name in self.servers:
            del self.servers[name]
            return True
        return False

    def get_group(self, group_name: str) -> List[ServerProfile]:
        """
        Get servers in a group.

        Args:
            group_name: Group name

        Returns:
            List of ServerProfile objects
        """
        server_names = self.groups.get(group_name, [])
        return [
            self.servers[name]
            for name in server_names
            if name in self.servers
        ]


# Global config instance
_config: Optional[TunnelShellConfig] = None


def get_config(reload: bool = False) -> TunnelShellConfig:
    """
    Get global configuration.

    Args:
        reload: Force reload from file

    Returns:
        TunnelShellConfig instance
    """
    global _config
    if _config is None or reload:
        _config = TunnelShellConfig.load()
    return _config


def create_default_config(path: Optional[str] = None) -> None:
    """
    Create default configuration file.

    Args:
        path: Config file path
    """
    config = TunnelShellConfig()

    # Add example server
    config.add_server(ServerProfile(
        name="example",
        host="example.com",
        port=22,
        user="user",
        tags=["example"],
        capabilities=["shell", "file_transfer"]
    ))

    # Set defaults
    config.defaults = {
        "timeout": 30,
        "connect_timeout": 10,
        "keepalive_interval": 15
    }

    config.save(path)