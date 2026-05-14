"""Exception hierarchy for TunnelShell.

This module defines a clear exception hierarchy for better error handling
and user-friendly error messages.
"""

from typing import Optional


class TunnelShellError(Exception):
    """Base exception for all TunnelShell errors.

    Attributes:
        message: Human-readable error message
        suggestion: Suggested action to resolve the error
        code: Error code for programmatic handling
    """

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        code: Optional[str] = None
    ):
        self.message = message
        self.suggestion = suggestion
        self.code = code or "UNKNOWN"
        super().__init__(self.message)

    def __str__(self) -> str:
        parts = [self.message]
        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")
        return "\n".join(parts)


# ============================================================================
# Connection Errors
# ============================================================================

class ConnectionError(TunnelShellError):
    """Base class for connection-related errors."""

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        code: str = "CONNECTION_ERROR"
    ):
        super().__init__(message, suggestion, code)


class AuthenticationError(ConnectionError):
    """Authentication failed (wrong password, invalid key, etc.)."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            suggestion="Check your SSH key or password. Ensure the key has correct permissions (chmod 600).",
            code="AUTH_ERROR"
        )


class HostKeyError(ConnectionError):
    """Host key verification failed."""

    def __init__(self, host: str):
        super().__init__(
            message=f"Host key verification failed for {host}",
            suggestion="Add the host to known_hosts or use StrictHostKeyChecking=no (not recommended for production).",
            code="HOST_KEY_ERROR"
        )


class ConnectionTimeoutError(ConnectionError):
    """Connection timed out."""

    def __init__(self, host: str, timeout: int):
        super().__init__(
            message=f"Connection to {host} timed out after {timeout}s",
            suggestion="Check if the host is reachable. Increase timeout or check network connectivity.",
            code="CONNECTION_TIMEOUT"
        )


# ============================================================================
# Session Errors
# ============================================================================

class SessionError(TunnelShellError):
    """Base class for session-related errors."""

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        code: str = "SESSION_ERROR"
    ):
        super().__init__(message, suggestion, code)


class SessionNotFoundError(SessionError):
    """Session does not exist."""

    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session '{session_id}' not found",
            suggestion="Use 'tunnel-shell session list' to see available sessions.",
            code="SESSION_NOT_FOUND"
        )


class SessionTimeoutError(SessionError):
    """Session operation timed out."""

    def __init__(self, session_id: str, timeout: int):
        super().__init__(
            message=f"Session '{session_id}' timed out after {timeout}s",
            suggestion="Increase timeout or check if the command is hanging.",
            code="SESSION_TIMEOUT"
        )


class SessionNotRunningError(SessionError):
    """Session is not in running state."""

    def __init__(self, session_id: str, status: str):
        super().__init__(
            message=f"Session '{session_id}' is not running (status: {status})",
            suggestion="Use 'tunnel-shell session attach' to start the session first.",
            code="SESSION_NOT_RUNNING"
        )


# ============================================================================
# Command Errors
# ============================================================================

class CommandError(TunnelShellError):
    """Base class for command-related errors."""

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        code: str = "COMMAND_ERROR",
        exit_code: Optional[int] = None
    ):
        self.exit_code = exit_code
        super().__init__(message, suggestion, code)


class CommandTimeoutError(CommandError):
    """Command execution timed out."""

    def __init__(self, command: str, timeout: int):
        super().__init__(
            message=f"Command '{command}' timed out after {timeout}s",
            suggestion="Increase command timeout or optimize the command.",
            code="COMMAND_TIMEOUT"
        )


class CommandFailedError(CommandError):
    """Command returned non-zero exit code."""

    def __init__(self, command: str, exit_code: int, output: str = ""):
        self.output = output
        super().__init__(
            message=f"Command '{command}' failed with exit code {exit_code}",
            suggestion="Check the command syntax and permissions. Review the output for details.",
            code="COMMAND_FAILED",
            exit_code=exit_code
        )


class CommandBlockedError(CommandError):
    """Command blocked by security policy."""

    def __init__(self, command: str, reason: str):
        super().__init__(
            message=f"Command '{command}' blocked: {reason}",
            suggestion="Review the command safety or adjust security policy.",
            code="COMMAND_BLOCKED"
        )


# ============================================================================
# Transfer Errors
# ============================================================================

class TransferError(TunnelShellError):
    """Base class for file transfer errors."""

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        code: str = "TRANSFER_ERROR"
    ):
        super().__init__(message, suggestion, code)


class UploadError(TransferError):
    """File upload failed."""

    def __init__(self, local_path: str, remote_path: str, reason: str = ""):
        super().__init__(
            message=f"Failed to upload '{local_path}' to '{remote_path}': {reason}",
            suggestion="Check local file exists and remote path is writable.",
            code="UPLOAD_ERROR"
        )


class DownloadError(TransferError):
    """File download failed."""

    def __init__(self, remote_path: str, local_path: str, reason: str = ""):
        super().__init__(
            message=f"Failed to download '{remote_path}' to '{local_path}': {reason}",
            suggestion="Check remote file exists and local path is writable.",
            code="DOWNLOAD_ERROR"
        )


class PathNotFoundError(TransferError):
    """Remote or local path does not exist."""

    def __init__(self, path: str, location: str = "remote"):
        super().__init__(
            message=f"{location.capitalize()} path '{path}' does not exist",
            suggestion=f"Verify the {location} path is correct.",
            code="PATH_NOT_FOUND"
        )


# ============================================================================
# Config Errors
# ============================================================================

class ConfigError(TunnelShellError):
    """Configuration error."""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        super().__init__(
            message=message,
            suggestion=suggestion or "Check your SSH config file (~/.ssh/config).",
            code="CONFIG_ERROR"
        )


class HostNotFoundError(ConfigError):
    """Host alias not found in SSH config."""

    def __init__(self, host: str):
        super().__init__(
            message=f"Host '{host}' not found in SSH config",
            suggestion=f"Add host configuration to ~/.ssh/config or use full hostname."
        )


class InvalidConfigError(ConfigError):
    """Invalid configuration value."""

    def __init__(self, field: str, value: str, reason: str = ""):
        super().__init__(
            message=f"Invalid config value for '{field}': {value}. {reason}",
            suggestion=f"Provide a valid value for '{field}'."
        )
