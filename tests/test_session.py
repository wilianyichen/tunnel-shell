"""Tests for session module."""

import pytest
from unittest.mock import Mock, patch
from tunnelshell.config import SSHConfig
from tunnelshell.session import PTYSession, SessionStatus


@pytest.fixture
def mock_config():
    """Create a mock SSH config."""
    return SSHConfig(host="example.com", port=22, user="testuser")


class TestPTYSession:
    """Tests for PTYSession class."""

    def test_session_create(self, mock_config):
        """Test creating a session."""
        session = PTYSession(session_id="test-session", config=mock_config)
        assert session.session_id == "test-session"
        assert session.config == mock_config
        assert session.status == SessionStatus.CREATED

    def test_session_with_name(self, mock_config):
        """Test creating a named session."""
        session = PTYSession(session_id="test-session", config=mock_config, name="my-session")
        assert session.name == "my-session"

    @patch("tunnelshell.session.Connection")
    def test_session_attach(self, mock_conn_class, mock_config):
        """Test attaching to session."""
        mock_conn = Mock()
        mock_conn.is_connected = True
        mock_conn._transport = Mock()
        mock_channel = Mock()
        mock_conn._transport.open_session.return_value = mock_channel
        mock_conn_class.return_value = mock_conn

        session = PTYSession(session_id="test-session", config=mock_config)
        session.attach()

        assert session.status == SessionStatus.RUNNING

    def test_session_kill(self, mock_config):
        """Test killing a session."""
        session = PTYSession(session_id="test-session", config=mock_config)
        session._channel = Mock()
        session._stop_event = Mock()

        session.kill()
        assert session.status == SessionStatus.KILLED
