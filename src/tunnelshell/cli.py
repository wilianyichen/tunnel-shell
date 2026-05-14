"""TunnelShell CLI - Agent-first remote terminal."""

import sys
import time
import threading
import re
import click
from datetime import datetime
from typing import Optional
from click import Context
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .version import __version__
from .config import SSHConfig
from .connection import Connection, ConnectionError, CommandError
from .session import PTYSession, SessionStatus
from .session_store import SessionStore
from .command_classifier import classify_command, CommandCategory
from .prompt_detector import detect_prompt, is_waiting_for_input
from .exceptions import TunnelShellError, AuthenticationError, ConnectionTimeoutError
from .output_parser import strip_ansi
from .file_transfer import FileTransfer, TransferProgress
from .timeout_manager import TimeoutManager, TimeoutConfig, TimeoutError
from .security import check_command_security, RiskLevel
from .recorder import SessionRecorder, SessionReplay, list_recordings, get_recording

# Disable Rich markup parsing to avoid issues with [str] etc.
console = Console(markup=False)

# Global session store
_store: SessionStore | None = None

def get_store() -> SessionStore:
    """Get or create the global session store."""
    global _store
    if _store is None:
        _store = SessionStore()
    return _store


def escape_for_shell(command: str) -> str:
    """Escape command for safe shell execution.
    
    This function ensures that special characters like [ ] * ? are properly
    escaped to prevent shell glob expansion, while preserving heredoc and
    other shell syntax.
    """
    # If the command is already quoted with single quotes, return as-is
    if command.startswith("'") and command.endswith("'"):
        return command
    
    # Escape special shell characters that cause glob expansion
    # But preserve heredoc syntax (<<) and other shell operators
    escaped = command.replace("\\", "\\\\")
    escaped = escaped.replace('"', '\\"')
    escaped = escaped.replace("$", "\\$")
    escaped = escaped.replace("`", "\\`")
    escaped = escaped.replace("(", "\\(")
    escaped = escaped.replace(")", "\\)")
    escaped = escaped.replace("[", "\\[")
    escaped = escaped.replace("]", "\\]")
    escaped = escaped.replace("*", "\\*")
    escaped = escaped.replace("?", "\\?")
    # Note: Do NOT escape <<, >>, |, &, ;, <, >, {, }
    # These are shell operators that should be preserved
    
    return escaped


@click.group()
@click.version_option(version=__version__, prog_name="tunnel-shell")
@click.option("--debug", is_flag=True, help="Enable debug output")
@click.pass_context
def main(ctx: click.Context, debug: bool) -> None:
    """TunnelShell - Agent-first remote terminal with persistent PTY sessions."""
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug


@main.command()
@click.option("--host", required=True, help="SSH host alias or hostname")
@click.option("--cmd", required=True, help="Command to execute")
@click.option("--timeout", default=30, help="Timeout in seconds")
@click.option("--raw", is_flag=True, help="Pass command to remote shell without any processing")
@click.option("--base64", is_flag=True, help="Decode base64 command before executing")
@click.pass_context
def exec(ctx: click.Context, host: str, cmd: str, timeout: int, raw: bool, base64: bool) -> None:
    """Execute a single command on a remote host."""
    debug = ctx.obj.get("debug", False)
    
    try:
        config = SSHConfig.from_host_alias(host, timeout=timeout)
        
        if debug:
            console.print(f"[dim]Host: {config.host}[/dim]")
            console.print(f"[dim]Port: {config.port}[/dim]")
            console.print(f"[dim]User: {config.user or 'default'}[/dim]")
        
        # Process command based on flags
        if base64:
            import base64
            try:
                cmd = base64.b64decode(cmd).decode("utf-8")
                if debug:
                    console.print(f"[dim]Decoded command: {cmd[:100]}...[/dim]")
            except Exception as e:
                console.print(f"[red]✗ Base64 decode failed:[/red] {e}")
                sys.exit(1)
        
        # Escape special characters for shell if not in raw mode
        if not raw:
            cmd = escape_for_shell(cmd)
            if debug:
                console.print(f"[dim]Escaped command: {cmd[:100]}...[/dim]")
        
        with Connection(config) as conn:
            console.print(f"[green]✓[/green] Connected to {host}")
            
            exit_code, stdout, stderr = conn.execute(cmd, timeout=timeout)
            
            if stdout:
                console.print(Panel(stdout.strip(), title="Output", border_style="green"))
            if stderr:
                console.print(Panel(stderr.strip(), title="Error", border_style="yellow"))
                
            if exit_code == 0:
                console.print(f"[green]✓[/green] Exit code: {exit_code}")
            else:
                console.print(f"[red]✗[/red] Exit code: {exit_code}")
                sys.exit(exit_code)
    except TunnelShellError as e:
        console.print(f"[red]✗ Error:[/red] {e.message}")
        if e.suggestion:
            console.print(f"[yellow]Suggestion:[/yellow] {e.suggestion}")
        sys.exit(1)
    except ConnectionError as e:
        console.print(f"[red]✗ Connection failed:[/red] {e}")
        sys.exit(1)
    except CommandError as e:
        console.print(f"[red]✗ Command failed:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Unexpected error:[/red] {e}")
        if debug:
            console.print_exception()
        sys.exit(1)

