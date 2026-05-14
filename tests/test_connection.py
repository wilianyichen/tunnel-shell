"""Tests for connection module."""

import pytest
from unittest.mock import Mock, patch
from tunnelshell.config import SSHConfig
from tunnelshell.connection import Connection


@pytest.fixture
def mock_config():
    """Create a mock SSH config."""
    return SSHConfig(host="example.com", port=22, user="testuser")


class TestConnection:
    """Tests for Connection class."""

    def test_connection_init(self, mock_config):
        """Test connection initialization."""
        conn = Connection(mock_config)
        assert conn.config == mock_config
        assert conn._client is None
        assert conn._connected == False

    def test_disconnect(self, mock_config):
        """Test disconnect."""
        conn = Connection(mock_config)
        mock_client = Mock()
        conn._client = mock_client
        conn._connected = True

        conn.disconnect()
        mock_client.close.assert_called_once()
        assert conn._connected == False
