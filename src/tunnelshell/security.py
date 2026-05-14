"""Security module for TunnelShell.

Provides command validation and dangerous operation detection.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Set


class RiskLevel(Enum):
    """Risk level for commands."""
    SAFE = "safe"               # No risk
    LOW = "low"                 # Minor risk, auto-approve
    MEDIUM = "medium"           # Moderate risk, require confirmation
    HIGH = "high"               # High risk, require explicit approval
    CRITICAL = "critical"       # Critical risk, block by default


@dataclass
class SecurityCheck:
    """Result of security check."""
    command: str
    risk_level: RiskLevel
    matched_patterns: List[str]
    warnings: List[str]
    blocked: bool
    reason: Optional[str] = None


class SecurityPolicy:
    """Security policy for command execution."""
    
    # Blocked patterns - always require explicit approval
    BLOCKED_PATTERNS = [
        (r"\brm\s+-rf\s+/(?!\S)", "rm -rf / - destroys entire filesystem"),
        (r"\brm\s+-rf\s+~", "rm -rf ~ - destroys home directory"),
        (r">\s*/dev/sd[a-z]", "Direct disk write"),
        (r"mkfs\.", "Format filesystem"),
        (r"dd\s+if=.*of=/dev/", "dd to disk device"),
        (r":\(\)\s*\{\s*:\|:&\s*\}\s*;", "Fork bomb"),
        (r"chmod\s+-R\s+777\s+/", "chmod 777 on root"),
        (r">\s*/etc/passwd", "Overwrite passwd file"),
        (r">\s*/etc/shadow", "Overwrite shadow file"),
        (r"curl.*\|\s*(ba)?sh", "Pipe curl to shell"),
        (r"wget.*\|\s*(ba)?sh", "Pipe wget to shell"),
    ]
    
    # High risk patterns
    HIGH_RISK_PATTERNS = [
        (r"\brm\s+-rf\b", "Recursive force delete"),
        (r"\bshutdown\b", "System shutdown"),
        (r"\breboot\b", "System reboot"),
        (r"\bpoweroff\b", "Power off system"),
        (r"\bhalt\b", "Halt system"),
        (r"\binit\s+[06]", "Change runlevel"),
        (r"\bkill\s+-9\s+1\b", "Kill init process"),
        (r"\biptables\s+-F\b", "Flush firewall rules"),
        (r"\buserdel\b", "Delete user"),
        (r"\bgroupdel\b", "Delete group"),
    ]
    
    # Medium risk patterns
    MEDIUM_RISK_PATTERNS = [
        (r"\bsudo\b", "Elevated privileges"),
        (r"\bsu\b", "Switch user"),
        (r"\bchmod\b", "Change permissions"),
        (r"\bchown\b", "Change ownership"),
        (r"\bkill\b", "Kill process"),
        (r"\bpkill\b", "Kill processes by name"),
        (r"\bmv\b.*\S+", "Move files"),
        (r"\bcp\b.*\S+", "Copy files"),
        (r"\bsystemctl\b", "System service control"),
        (r"\bservice\b", "Service control"),
    ]
    
    # Safe commands (whitelist)
    SAFE_COMMANDS: Set[str] = {
        "ls", "dir", "pwd", "whoami", "hostname", "uname",
        "cat", "head", "tail", "less", "more", "wc",
        "grep", "find", "locate", "which", "whereis",
        "echo", "printf", "date", "cal",
        "df", "du", "free", "top", "htop", "ps",
        "git", "svn", "hg",
        "python", "python3", "node", "ruby", "perl",
        "pip", "npm", "gem", "cargo",
    }
    
    def __init__(
        self,
        block_critical: bool = True,
        require_approval_high: bool = True,
        require_approval_medium: bool = False,
    ):
        self.block_critical = block_critical
        self.require_approval_high = require_approval_high
        self.require_approval_medium = require_approval_medium
        
    def check(self, command: str) -> SecurityCheck:
        """Check command for security risks."""
        matched_patterns = []
        warnings = []
        risk_level = RiskLevel.SAFE
        
        # Check blocked patterns
        for pattern, description in self.BLOCKED_PATTERNS:
            if re.search(pattern, command):
                matched_patterns.append(pattern)
                warnings.append(description)
                risk_level = RiskLevel.CRITICAL
                
        # Check high risk patterns
        if risk_level != RiskLevel.CRITICAL:
            for pattern, description in self.HIGH_RISK_PATTERNS:
                if re.search(pattern, command):
                    matched_patterns.append(pattern)
                    warnings.append(description)
                    risk_level = RiskLevel.HIGH
                    
        # Check medium risk patterns
        if risk_level in (RiskLevel.SAFE, RiskLevel.LOW):
            for pattern, description in self.MEDIUM_RISK_PATTERNS:
                if re.search(pattern, command):
                    matched_patterns.append(pattern)
                    warnings.append(description)
                    risk_level = RiskLevel.MEDIUM
                    
        # Check if command is in safe list
        cmd_parts = command.split()
        if cmd_parts and cmd_parts[0] in self.SAFE_COMMANDS:
            if risk_level == RiskLevel.SAFE:
                risk_level = RiskLevel.SAFE
                
        # Determine if blocked
        blocked = False
        reason = None
        
        if risk_level == RiskLevel.CRITICAL and self.block_critical:
            blocked = True
            reason = "Command matches blocked pattern"
            
        return SecurityCheck(
            command=command,
            risk_level=risk_level,
            matched_patterns=matched_patterns,
            warnings=warnings,
            blocked=blocked,
            reason=reason,
        )
        
    def is_safe(self, command: str) -> bool:
        """Quick check if command is safe."""
        check = self.check(command)
        return check.risk_level in (RiskLevel.SAFE, RiskLevel.LOW)
        
    def needs_approval(self, command: str) -> bool:
        """Check if command needs approval."""
        check = self.check(command)
        
        if check.risk_level == RiskLevel.HIGH and self.require_approval_high:
            return True
        if check.risk_level == RiskLevel.MEDIUM and self.require_approval_medium:
            return True
            
        return False


# Default security policy
DEFAULT_SECURITY_POLICY = SecurityPolicy()


def check_command_security(command: str) -> SecurityCheck:
    """Check command security with default policy."""
    return DEFAULT_SECURITY_POLICY.check(command)


def is_command_safe(command: str) -> bool:
    """Quick check if command is safe."""
    return DEFAULT_SECURITY_POLICY.is_safe(command)