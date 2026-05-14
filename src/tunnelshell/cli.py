"""TunnelShell CLI - Agent-first remote terminal."""

import sys
import time
import threading
import re
from datetime import datetime
from typing import Optional
import click
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

console = Console()

# Global session store
_store: SessionStore | None = None

def get_store() -> SessionStore:
    """Get or create the global session store."""
    global _store
    if _store is None:
        _store = SessionStore()
    return _store


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
@click.pass_context
def exec(ctx: click.Context, host: str, cmd: str, timeout: int) -> None:
    """Execute a single command on a remote host."""
    debug = ctx.obj.get("debug", False)
    
    try:
        config = SSHConfig.from_host_alias(host, timeout=timeout)
        
        if debug:
            console.print(f"[dim]Host: {config.host}[/dim]")
            console.print(f"[dim]Port: {config.port}[/dim]")
            console.print(f"[dim]User: {config.user or 'default'}[/dim]")
        
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
        sys.exit(1)


@main.group()
def session() -> None:
    """Manage persistent PTY sessions."""
    pass


@session.command("create")
@click.option("--host", required=True, help="SSH host alias or hostname")
@click.option("--name", help="Session name (auto-generated if not provided)")
@click.pass_context
def session_create(ctx: click.Context, host: str, name: str | None) -> None:
    """Create a new persistent session."""
    debug = ctx.obj.get("debug", False)
    
    try:
        config = SSHConfig.from_host_alias(host)
        store = get_store()
        
        session = store.create(config, name=name)
        console.print(f"[green]✓[/green] Created session: {session.session_id}")
        if name:
            console.print(f"  Name: {name}")
        console.print(f"  Host: {host}")
        console.print(f"\nUse 'tunnel-shell session attach --name {name or session.session_id}' to connect")
        
    except Exception as e:
        console.print(f"[red]✗ Failed to create session:[/red] {e}")
        if debug:
            console.print_exception()
        sys.exit(1)


@session.command("attach")
@click.option("--name", help="Session name to attach to")
@click.option("--host", help="SSH host (if creating new session)")
@click.option("--cmd", help="Execute command and exit (non-interactive)")
@click.pass_context
def session_attach(ctx: click.Context, name: str | None, host: str | None, cmd: str | None) -> None:
    """Attach to an existing session or create a new one."""
    debug = ctx.obj.get("debug", False)
    store = get_store()
    
    try:
        session_obj = None
        if name:
            session_obj = store.get_by_name(name) or store.get(name)
            
        if not session_obj and host:
            config = SSHConfig.from_host_alias(host)
            session_obj = store.create(config, name=name)
            console.print(f"[green]✓[/green] Created new session: {session_obj.session_id}")
        elif not session_obj:
            console.print("[red]✗ Session not found. Use --host to create a new session.[/red]")
            sys.exit(1)
            
        console.print(f"[yellow]Connecting to {session_obj.config.host}...[/yellow]")
        session_obj.attach()
        
        # Update status to running
        store.update_status(session_obj.session_id, SessionStatus.RUNNING)
        
        console.print(f"[green]✓[/green] Connected! Session is running.")
        console.print(f"[dim]Press Ctrl+C to detach (session keeps running)[/dim]\n")
        
        if cmd:
            session_obj.send_line(cmd)
            
            time.sleep(1.0)
            for _ in range(5):
                output = session_obj.snapshot()
                if output:
                    break
                time.sleep(0.5)
                
            if output:
                clean_output = re.sub(r'\x1b\[[0-9;]*[mGKH]', '', output)
                console.print(clean_output)
                
            session_obj.detach()
            store.update_status(session_obj.session_id, SessionStatus.DETACHED)
        else:
            _interactive_session(session_obj, store, debug)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Detached from session (session keeps running)[/yellow]")
        if session_obj:
            store.update_status(session_obj.session_id, SessionStatus.DETACHED)
    except Exception as e:
        console.print(f"[red]✗ Failed to attach:[/red] {e}")
        if debug:
            console.print_exception()
        sys.exit(1)


def _interactive_session(session_obj: PTYSession, store: SessionStore, debug: bool = False) -> None:
    """Run interactive PTY session with live output display."""
    
    output_buffer = []
    
    def read_output():
        while session_obj.status == SessionStatus.RUNNING:
            output = session_obj.read_output(timeout=0.1)
            if output:
                output_buffer.append(output)
                
    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    
    try:
        while session_obj.status == SessionStatus.RUNNING:
            if output_buffer:
                console.print("".join(output_buffer), end="")
                output_buffer.clear()
            time.sleep(0.05)
    except KeyboardInterrupt:
        session_obj.detach()
        store.update_status(session_obj.session_id, SessionStatus.DETACHED)


@session.command("list")
@click.pass_context
def session_list(ctx: click.Context) -> None:
    """List all active sessions."""
    store = get_store()
    sessions = store.list()
    
    if not sessions:
        console.print("[yellow]No active sessions[/yellow]")
        return
        
    table = Table(title="Active Sessions")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Host", style="blue")
    table.add_column("Status", style="yellow")
    table.add_column("Created", style="dim")
    
    for info in sessions:
        table.add_row(
            info.session_id,
            info.name or "-",
            info.host,
            info.status.value,
            time.strftime("%H:%M:%S", time.localtime(info.created_at)),
        )
        
    console.print(table)


@session.command("kill")
@click.option("--name", default="", help="Session name or ID to kill")
@click.option("--all", "kill_all", is_flag=True, help="Kill all sessions")
@click.pass_context
def session_kill(ctx: click.Context, name: str, kill_all: bool) -> None:
    """Kill a session."""
    store = get_store()
    
    if kill_all:
        count = 0
        for info in store.list():
            if store.kill(info.session_id):
                count += 1
        console.print(f"[green]✓[/green] Killed {count} sessions")
    elif name:
        if store.kill_by_name(name) or store.kill(name):
            console.print(f"[green]✓[/green] Killed session: {name}")
        else:
            console.print(f"[red]✗ Session not found: {name}[/red]")
            sys.exit(1)
    else:
        console.print("[red]✗ Please specify --name or --all[/red]")
        sys.exit(1)


@main.command()
@click.argument("command")
@click.pass_context
def analyze(ctx: click.Context, command: str) -> None:
    """Analyze a command for classification and safety."""
    info = classify_command(command)
    security = check_command_security(command)
    
    console.print(f"\n[bold]Command Analysis[/bold]")
    console.print(f"  Raw: {info.raw}")
    console.print(f"  Command: {info.command}")
    console.print(f"  Args: {info.args}")
    console.print(f"  Category: {info.category.value}")
    
    # Security info
    console.print(f"\n[bold]Security Check[/bold]")
    console.print(f"  Risk Level: {security.risk_level.value}")
    
    if security.warnings:
        console.print(f"  Warnings:")
        for w in security.warnings:
            console.print(f"    [yellow]⚠ {w}[/yellow]")
            
    if security.blocked:
        console.print(f"  [red]✗ BLOCKED: {security.reason}[/red]")
    elif security.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
        console.print(f"  [yellow]⚠ Requires approval[/yellow]")
    else:
        console.print(f"  [green]✓ Safe to execute[/green]")
        
    if info.timeout_hint:
        console.print(f"\n  Timeout hint: {info.timeout_hint}s")


@main.command()
@click.argument("text")
@click.pass_context
def detect(ctx: click.Context, text: str) -> None:
    """Detect interactive prompts in text."""
    prompt = detect_prompt(text)
    
    if prompt:
        console.print(f"\n[bold green]✓ Prompt Detected[/bold green]")
        console.print(f"  Type: {prompt.prompt_type.value}")
        console.print(f"  Text: {prompt.text}")
        if prompt.suggested_response is not None:
            console.print(f"  Suggested response: {prompt.suggested_response}")
    else:
        console.print("\n[yellow]No prompt detected[/yellow]")


@main.group()
def file() -> None:
    """File transfer operations."""
    pass


@file.command("upload")
@click.option("--host", required=True, help="SSH host alias or hostname")
@click.option("--local", required=True, help="Local file path")
@click.option("--remote", required=True, help="Remote file path")
@click.pass_context
def file_upload(ctx: click.Context, host: str, local: str, remote: str) -> None:
    """Upload a file to remote server."""
    try:
        config = SSHConfig.from_host_alias(host)
        
        with FileTransfer(config) as transfer:
            console.print(f"[yellow]Uploading {local} -> {remote}...[/yellow]")
            
            def show_progress(p: TransferProgress) -> None:
                percent = p.percent
                bar_len = 30
                filled = int(bar_len * percent / 100)
                bar = "█" * filled + "░" * (bar_len - filled)
                speed_mb = p.speed / 1024 / 1024
                console.print(
                    f"\r[{bar}] {percent:.1f}% ({p.transferred_bytes}/{p.total_bytes} bytes, {speed_mb:.1f} MB/s)",
                    end=""
                )
            
            result = transfer.upload(local, remote, progress_callback=show_progress)
            console.print()
            
            console.print(f"[green]✓[/green] Uploaded {result.transferred_bytes} bytes")
            
    except Exception as e:
        console.print(f"\n[red]✗ Upload failed:[/red] {e}")
        sys.exit(1)


@file.command("download")
@click.option("--host", required=True, help="SSH host alias or hostname")
@click.option("--remote", required=True, help="Remote file path")
@click.option("--local", required=True, help="Local file path")
@click.pass_context
def file_download(ctx: click.Context, host: str, remote: str, local: str) -> None:
    """Download a file from remote server."""
    try:
        config = SSHConfig.from_host_alias(host)
        
        with FileTransfer(config) as transfer:
            console.print(f"[yellow]Downloading {remote} -> {local}...[/yellow]")
            
            def show_progress(p: TransferProgress) -> None:
                percent = p.percent
                bar_len = 30
                filled = int(bar_len * percent / 100)
                bar = "█" * filled + "░" * (bar_len - filled)
                speed_mb = p.speed / 1024 / 1024
                console.print(
                    f"\r[{bar}] {percent:.1f}% ({p.transferred_bytes}/{p.total_bytes} bytes, {speed_mb:.1f} MB/s)",
                    end=""
                )
            
            result = transfer.download(remote, local, progress_callback=show_progress)
            console.print()
            
            console.print(f"[green]✓[/green] Downloaded {result.transferred_bytes} bytes")
            
    except Exception as e:
        console.print(f"\n[red]✗ Download failed:[/red] {e}")
        sys.exit(1)


@file.command("list")
@click.option("--host", required=True, help="SSH host alias or hostname")
@click.option("--path", default=".", help="Remote directory path")
@click.pass_context
def file_list(ctx: click.Context, host: str, path: str) -> None:
    """List files in remote directory."""
    try:
        config = SSHConfig.from_host_alias(host)
        
        with FileTransfer(config) as transfer:
            files = transfer.list_dir(path)
            
            table = Table(title=f"Remote: {path}")
            table.add_column("Name", style="cyan")
            
            for f in sorted(files):
                table.add_row(f)
                
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]✗ List failed:[/red] {e}")
        sys.exit(1)


@main.group()
def recording() -> None:
    """Session recording operations."""
    pass


@recording.command("list")
@click.pass_context
def recording_list(ctx: click.Context) -> None:
    """List all recordings."""
    recordings = list_recordings()
    
    if not recordings:
        console.print("[yellow]No recordings found[/yellow]")
        return
        
    table = Table(title="Session Recordings")
    table.add_column("Session ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Host", style="blue")
    table.add_column("Duration", style="yellow")
    table.add_column("Events", style="dim")
    table.add_column("Date", style="dim")
    
    for r in recordings:
        duration = r.get('duration', 0)
        table.add_row(
            r.get('session_id', '-'),
            r.get('session_name') or '-',
            r.get('host', '-'),
            f"{duration:.1f}s",
            str(r.get('event_count', 0)),
            datetime.fromtimestamp(r.get('start_time', 0)).strftime("%Y-%m-%d %H:%M"),
        )
        
    console.print(table)


@recording.command("show")
@click.argument("session_id")
@click.pass_context
def recording_show(ctx: click.Context, session_id: str) -> None:
    """Show recording details."""
    replay = get_recording(session_id)
    
    if not replay:
        console.print(f"[red]✗ Recording not found: {session_id}[/red]")
        sys.exit(1)
        
    replay.load()
    meta = replay.metadata
    
    if meta:
        console.print(f"\n[bold]Recording: {session_id}[/bold]")
        console.print(f"  Name: {meta.session_name or '-'}")
        console.print(f"  Host: {meta.host}")
        console.print(f"  Duration: {meta.duration:.1f}s")
        console.print(f"  Events: {meta.event_count}")
        console.print(f"  File size: {meta.file_size} bytes")
        
    console.print(f"\n[bold]Timeline:[/bold]")
    for event in replay.get_timeline()[:20]:  # Show first 20 events
        console.print(f"  [{event['type']}] {event['preview']}")
        
    if len(replay.events) > 20:
        console.print(f"  ... and {len(replay.events) - 20} more events")


@recording.command("export")
@click.argument("session_id")
@click.option("--output", "-o", help="Output file path")
@click.pass_context
def recording_export(ctx: click.Context, session_id: str, output: Optional[str]) -> None:
    """Export recording output to file."""
    replay = get_recording(session_id)
    
    if not replay:
        console.print(f"[red]✗ Recording not found: {session_id}[/red]")
        sys.exit(1)
        
    replay.load()
    
    output_path = output or f"{session_id}.txt"
    output_text = replay.get_output()
    
    with open(output_path, 'w') as f:
        f.write(output_text)
        
    console.print(f"[green]✓[/green] Exported to {output_path} ({len(output_text)} bytes)")


if __name__ == "__main__":
    main()