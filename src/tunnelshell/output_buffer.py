"""Output buffer management for PTY sessions."""

import re
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class OutputBuffer:
    """Manages PTY output with buffering and ANSI processing."""
    
    max_lines: int = 1000
    max_bytes: int = 1024 * 1024  # 1MB
    
    _buffer: deque = field(default_factory=lambda: deque(maxlen=1000))
    _total_bytes: int = 0
    _raw_buffer: str = ""
    
    def append(self, data: str) -> None:
        """Append output data to buffer."""
        self._raw_buffer += data
        self._total_bytes += len(data)
        
        # Split into lines and add to buffer
        lines = data.split("\n")
        for line in lines:
            if line:
                self._buffer.append(line)
                
        # Trim if exceeds max bytes
        if self._total_bytes > self.max_bytes:
            self._trim()
            
    def _trim(self) -> None:
        """Trim buffer to stay within limits."""
        while self._buffer and self._total_bytes > self.max_bytes:
            removed = self._buffer.popleft()
            self._total_bytes -= len(removed)
            
    def get_recent(self, lines: int = 50) -> str:
        """Get recent N lines from buffer."""
        recent = list(self._buffer)[-lines:]
        return "\n".join(recent)
        
    def get_all(self) -> str:
        """Get all buffered output."""
        return "\n".join(self._buffer)
        
    def clear(self) -> None:
        """Clear the buffer."""
        self._buffer.clear()
        self._raw_buffer = ""
        self._total_bytes = 0
        
    @staticmethod
    def strip_ansi(text: str) -> str:
        """Remove ANSI escape sequences from text."""
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*[mGKHJ]')
        return ansi_pattern.sub('', text)
        
    @staticmethod
    def detect_prompt(text: str) -> Optional[str]:
        """Detect if output contains an interactive prompt.
        
        Returns the prompt type if detected, None otherwise.
        """
        prompt_patterns = {
            "password": [
                r"[Pp]assword\s*:",
                r"[Pp]assphrase\s*:",
                r"Enter password:",
            ],
            "confirm": [
                r"\(y/n\)",
                r"\[y/n\]",
                r"\(yes/no\)",
                r"\[yes/no\]",
                r"Continue\?",
                r"Overwrite\?",
                r"Are you sure\?",
            ],
            "input": [
                r"Enter\s+.*:",
                r"Input\s+.*:",
                r"Please enter",
            ],
        }
        
        last_line = text.strip().split("\n")[-1] if text else ""
        
        for prompt_type, patterns in prompt_patterns.items():
            for pattern in patterns:
                if re.search(pattern, last_line, re.IGNORECASE):
                    return prompt_type
                    
        return None
        
    def get_stats(self) -> dict:
        """Get buffer statistics."""
        return {
            "lines": len(self._buffer),
            "bytes": self._total_bytes,
            "max_lines": self.max_lines,
            "max_bytes": self.max_bytes,
        }