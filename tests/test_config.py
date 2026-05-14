"""Tests for config module."""

import pytest
from tunnelshell.config import SSHConfig


class TestSSHConfig:
    """Tests for SSHConfig class."""

    def test_ssh_config_defaults(self):
        """Test default values."""
        config = SSHConfig(host="example.com")
        assert config.host == "example.com"
        assert config.port == 22
        assert config.user is None

    def test_ssh_config_custom_values(self):
        """Test custom values."""
        config = SSHConfig(
            host="example.com",
            port=2222,
            user="testuser",
            timeout=60
        )
        assert config.host == "example.com"
        assert config.port == 2222
        assert config.user == "testuser"
        assert config.timeout == 60

    def test_ssh_config_from_user_host_port(self):
        """Test parsing user@host:port format."""
        config = SSHConfig.from_host_alias("testuser@example.com:2222")
        assert config.host == "example.com"
        assert config.port == 2222
        assert config.user == "testuser"

    def test_ssh_config_from_host_port(self):
        """Test parsing host:port format."""
        config = SSHConfig.from_host_alias("example.com:2222")
        assert config.host == "example.com"
        assert config.port == 2222

    def test_ssh_config_from_host_only(self):
        """Test parsing host only."""
        config = SSHConfig.from_host_alias("example.com")
        assert config.host == "example.com"
        assert config.port == 22
