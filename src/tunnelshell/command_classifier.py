"""Command classifier for TunnelShell.

Classifies commands into categories for better handling and display.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Set


class CommandCategory(Enum):
    """Command category for handling strategy."""
    SEARCH = "search"       # Find/grep commands - stream output
    READ = "read"           # Cat/head/tail - show full output
    SILENT = "silent"       # Mv/cp/rm - only show status
    INTERACTIVE = "interactive"  # Vim/top - needs special handling
    STATEFUL = "stateful"   # Cd/export - changes session state
    UNKNOWN = "unknown"     # Unknown command


@dataclass
class CommandInfo:
    """Parsed command information."""
    raw: str
    command: str
    args: list[str]
    category: CommandCategory
    is_dangerous: bool = False
    needs_confirmation: bool = False
    timeout_hint: Optional[int] = None


class CommandClassifier:
    """Classifies shell commands into categories."""
    
    # Search commands - typically produce lots of output
    SEARCH_COMMANDS: Set[str] = {
        "find", "grep", "rg", "ag", "ack", "locate", 
        "which", "whereis", "fd",
    }
    
    # Read commands - show file contents
    READ_COMMANDS: Set[str] = {
        "cat", "head", "tail", "less", "more", "wc", 
        "stat", "file", "strings", "jq", "awk", "cut",
        "sort", "uniq", "tr", "sed", "nl", "od", "hexdump",
    }
    
    # Silent commands - success means no output
    SILENT_COMMANDS: Set[str] = {
        "mv", "cp", "rm", "mkdir", "rmdir", "chmod", "chown",
        "touch", "ln", "rename", "install", "truncate",
    }
    
    # Interactive commands - need PTY
    INTERACTIVE_COMMANDS: Set[str] = {
        "vim", "vi", "nano", "emacs", "less", "more",
        "top", "htop", "btop", "glances",
        "screen", "tmux", "byobu",
        "man", "info",
        "python", "python3", "ipython", "node", "irb",
        "mysql", "psql", "sqlite3", "redis-cli",
        "ssh", "scp", "rsync", "sftp",
        "sudo", "su", "doas",
        "watch", "dialog", "whiptail",
    }
    
    # Stateful commands - change session state
    STATEFUL_COMMANDS: Set[str] = {
        "cd", "pushd", "popd", "dirs",
        "export", "unset", "set", "source", ".",
        "alias", "unalias",
        "umask", "ulimit",
    }
    
    # Dangerous patterns
    DANGEROUS_PATTERNS = [
        (r"\brm\s+-rf\s+/(?!\S)", "rm -rf /"),
        (r"\brm\s+-rf\s+~", "rm -rf ~"),
        (r">\s*/dev/sd[a-z]", "overwrite disk"),
        (r"mkfs\.", "format filesystem"),
        (r"dd\s+if=.*of=/dev/", "dd to disk"),
        (r":(){ :\|:& };:", "fork bomb"),
        (r"chmod\s+-R\s+777\s+/", "chmod 777 /"),
        (r">\s*/etc/passwd", "overwrite passwd"),
        (r">\s>/etc/shadow", "overwrite shadow"),
    ]
    
    # Commands needing confirmation
    CONFIRMATION_PATTERNS = [
        r"\brm\b",       # rm
        r"\bmv\b.*\S+",  # mv with destination
        r"\bchmod\b",    # chmod
        r"\bchown\b",    # chown
        r"\bkill\b",     # kill
        r"\bpkill\b",    # pkill
        r"\bshutdown\b", # shutdown
        r"\breboot\b",   # reboot
        r"\bpoweroff\b", # poweroff
    ]
    
    def classify(self, command: str) -> CommandInfo:
        """Classify a command string."""
        # Parse command
        parts = self._parse_command(command)
        if not parts:
            return CommandInfo(
                raw=command,
                command="",
                args=[],
                category=CommandCategory.UNKNOWN,
            )
        
        cmd = parts[0]
        args = parts[1:]
        
        # Determine category
        category = self._get_category(cmd, args)
        
        # Check for dangerous patterns
        is_dangerous = self._check_dangerous(command)
        
        # Check if needs confirmation
        needs_confirmation = self._check_confirmation(command)
        
        # Estimate timeout
        timeout_hint = self._estimate_timeout(cmd, args)
        
        return CommandInfo(
            raw=command,
            command=cmd,
            args=args,
            category=category,
            is_dangerous=is_dangerous,
            needs_confirmation=needs_confirmation,
            timeout_hint=timeout_hint,
        )
    
    def _parse_command(self, command: str) -> list[str]:
        """Parse command into parts, handling quotes."""
        # Simple split - could be improved with shlex
        try:
            import shlex
            return shlex.split(command)
        except ValueError:
            return command.split()
    
    def _get_category(self, cmd: str, args: list[str]) -> CommandCategory:
        """Determine command category."""
        # Check each category
        if cmd in self.SEARCH_COMMANDS:
            return CommandCategory.SEARCH
        if cmd in self.READ_COMMANDS:
            return CommandCategory.READ
        if cmd in self.SILENT_COMMANDS:
            return CommandCategory.SILENT
        if cmd in self.INTERACTIVE_COMMANDS:
            return CommandCategory.INTERACTIVE
        if cmd in self.STATEFUL_COMMANDS:
            return CommandCategory.STATEFUL
        
        # Check for pipes/redirections that might indicate read
        if "|" in " ".join(args) or "<" in " ".join(args):
            return CommandCategory.READ
        
        return CommandCategory.UNKNOWN
    
    def _check_dangerous(self, command: str) -> bool:
        """Check if command matches dangerous patterns."""
        for pattern, _ in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command):
                return True
        return False
    
    def _check_confirmation(self, command: str) -> bool:
        """Check if command should prompt for confirmation."""
        for pattern in self.CONFIRMATION_PATTERNS:
            if re.search(pattern, command):
                return True
        return False
    
    def _estimate_timeout(self, cmd: str, args: list[str]) -> Optional[int]:
        """Estimate appropriate timeout for command."""
        # Long-running commands
        long_commands = {"find", "grep", "rg", "tar", "rsync", "scp", "dd"}
        if cmd in long_commands:
            return 300  # 5 minutes
        
        # Quick commands
        quick_commands = {"ls", "pwd", "whoami", "hostname", "echo", "cat"}
        if cmd in quick_commands:
            return 10  # 10 seconds
        
        return None  # Use default


# Global classifier instance
_classifier = CommandClassifier()


def classify_command(command: str) -> CommandInfo:
    """Classify a command string."""
    return _classifier.classify(command)