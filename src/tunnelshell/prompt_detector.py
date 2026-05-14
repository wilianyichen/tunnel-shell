"""Prompt detector for TunnelShell.

Detects interactive prompts in terminal output.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List


class PromptType(Enum):
    """Type of interactive prompt detected."""
    PASSWORD = "password"
    PASSPHRASE = "passphrase"
    CONFIRM_YES_NO = "confirm_yes_no"
    CONFIRM_CONTINUE = "confirm_continue"
    INPUT_REQUIRED = "input_required"
    SELECT_OPTION = "select_option"
    UNKNOWN = "unknown"


@dataclass
class PromptMatch:
    """A detected prompt match."""
    prompt_type: PromptType
    pattern: str
    text: str
    line_number: int
    suggested_response: Optional[str] = None


class PromptDetector:
    """Detects interactive prompts in terminal output."""
    
    # Password prompts
    PASSWORD_PATTERNS = [
        (r"[Pp]assword\s*:", PromptType.PASSWORD),
        (r"[Pp]assword\s+for\s+.*:", PromptType.PASSWORD),
        (r"Enter\s+[Pp]assword:", PromptType.PASSWORD),
        (r"[Pp]assphrase\s*:", PromptType.PASSPHRASE),
        (r"Enter\s+passphrase\s+for\s+.*:", PromptType.PASSPHRASE),
        (r"PIN\s*:", PromptType.PASSWORD),
    ]
    
    # Yes/No confirmation prompts
    CONFIRM_PATTERNS = [
        (r"\(y/n\)\s*$", PromptType.CONFIRM_YES_NO, "n"),
        (r"\[y/n\]\s*$", PromptType.CONFIRM_YES_NO, "n"),
        (r"\(yes/no\)\s*$", PromptType.CONFIRM_YES_NO, "no"),
        (r"\[yes/no\]\s*$", PromptType.CONFIRM_YES_NO, "no"),
        (r"\[Y/n\]\s*$", PromptType.CONFIRM_YES_NO, "n"),
        (r"\[y/N\]\s*$", PromptType.CONFIRM_YES_NO, "N"),
        (r"\(Y/n\)\s*$", PromptType.CONFIRM_YES_NO, "n"),
        (r"\(y/N\)\s*$", PromptType.CONFIRM_YES_NO, "N"),
    ]
    
    # Continue prompts
    CONTINUE_PATTERNS = [
        (r"Continue\s*\?\s*$", PromptType.CONFIRM_CONTINUE),
        (r"Do\s+you\s+want\s+to\s+continue\s*\?\s*$", PromptType.CONFIRM_CONTINUE),
        (r"Are\s+you\s+sure\s+you\s+want\s+to\s+.*\?\s*$", PromptType.CONFIRM_CONTINUE),
        (r"Proceed\s*\?\s*$", PromptType.CONFIRM_CONTINUE),
        (r"Overwrite\s*\?\s*$", PromptType.CONFIRM_CONTINUE),
        (r"Replace\s*\?\s*$", PromptType.CONFIRM_CONTINUE),
        (r"Press\s+(any\s+key|Enter)\s+to\s+continue", PromptType.CONFIRM_CONTINUE, ""),
        (r"Press\s+.*\s+to\s+.*\s*$", PromptType.CONFIRM_CONTINUE),
    ]
    
    # Input prompts
    INPUT_PATTERNS = [
        (r"Enter\s+.*:\s*$", PromptType.INPUT_REQUIRED),
        (r"Input\s+.*:\s*$", PromptType.INPUT_REQUIRED),
        (r"Please\s+enter\s+.*:\s*$", PromptType.INPUT_REQUIRED),
        (r"Provide\s+.*:\s*$", PromptType.INPUT_REQUIRED),
        (r"Username\s*:", PromptType.INPUT_REQUIRED),
        (r"Login\s*:", PromptType.INPUT_REQUIRED),
        (r"Email\s*:", PromptType.INPUT_REQUIRED),
    ]
    
    # Select option prompts
    SELECT_PATTERNS = [
        (r"Select\s+.*:\s*$", PromptType.SELECT_OPTION),
        (r"Choose\s+.*:\s*$", PromptType.SELECT_OPTION),
        (r"Pick\s+.*:\s*$", PromptType.SELECT_OPTION),
        (r"\[\d+\].*", PromptType.SELECT_OPTION),  # [1] option [2] option
        (r"Enter\s+selection\s*:", PromptType.SELECT_OPTION),
        (r"Enter\s+choice\s*:", PromptType.SELECT_OPTION),
    ]
    
    def detect(self, output: str) -> Optional[PromptMatch]:
        """Detect if output contains an interactive prompt.
        
        Returns the most recent prompt match, or None if no prompt detected.
        """
        lines = output.split("\n")
        matches = []
        
        for i, line in enumerate(lines):
            # Check password patterns
            for pattern, prompt_type in self.PASSWORD_PATTERNS:
                if re.search(pattern, line):
                    matches.append(PromptMatch(
                        prompt_type=prompt_type,
                        pattern=pattern,
                        text=line,
                        line_number=i,
                    ))
            
            # Check confirmation patterns
            for pattern, prompt_type, suggested in self.CONFIRM_PATTERNS:
                if re.search(pattern, line):
                    matches.append(PromptMatch(
                        prompt_type=prompt_type,
                        pattern=pattern,
                        text=line,
                        line_number=i,
                        suggested_response=suggested,
                    ))
            
            # Check continue patterns
            for item in self.CONTINUE_PATTERNS:
                if len(item) == 2:
                    pattern, prompt_type = item
                    suggested = None
                else:
                    pattern, prompt_type, suggested = item
                if re.search(pattern, line):
                    matches.append(PromptMatch(
                        prompt_type=prompt_type,
                        pattern=pattern,
                        text=line,
                        line_number=i,
                        suggested_response=suggested,
                    ))
            
            # Check input patterns
            for pattern, prompt_type in self.INPUT_PATTERNS:
                if re.search(pattern, line):
                    matches.append(PromptMatch(
                        prompt_type=prompt_type,
                        pattern=pattern,
                        text=line,
                        line_number=i,
                    ))
            
            # Check select patterns
            for pattern, prompt_type in self.SELECT_PATTERNS:
                if re.search(pattern, line):
                    matches.append(PromptMatch(
                        prompt_type=prompt_type,
                        pattern=pattern,
                        text=line,
                        line_number=i,
                    ))
        
        # Return most recent match (last line)
        if matches:
            return max(matches, key=lambda m: m.line_number)
        return None
    
    def detect_all(self, output: str) -> List[PromptMatch]:
        """Detect all prompts in output."""
        lines = output.split("\n")
        matches = []
        
        for i, line in enumerate(lines):
            # Check all patterns (same logic as detect)
            for pattern, prompt_type in self.PASSWORD_PATTERNS:
                if re.search(pattern, line):
                    matches.append(PromptMatch(
                        prompt_type=prompt_type,
                        pattern=pattern,
                        text=line,
                        line_number=i,
                    ))
            
            for item in self.CONFIRM_PATTERNS:
                if len(item) == 2:
                    pattern, prompt_type = item
                    suggested = None
                else:
                    pattern, prompt_type, suggested = item
                if re.search(pattern, line):
                    matches.append(PromptMatch(
                        prompt_type=prompt_type,
                        pattern=pattern,
                        text=line,
                        line_number=i,
                        suggested_response=suggested,
                    ))
        
        return matches
    
    def is_waiting_for_input(self, output: str) -> bool:
        """Check if terminal is waiting for user input."""
        return self.detect(output) is not None
    
    def get_prompt_type(self, output: str) -> Optional[PromptType]:
        """Get the type of prompt if detected."""
        match = self.detect(output)
        return match.prompt_type if match else None


# Global detector instance
_detector = PromptDetector()


def detect_prompt(output: str) -> Optional[PromptMatch]:
    """Detect interactive prompt in output."""
    return _detector.detect(output)


def is_waiting_for_input(output: str) -> bool:
    """Check if output contains a prompt waiting for input."""
    return _detector.is_waiting_for_input(output)