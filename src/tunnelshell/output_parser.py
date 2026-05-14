"""ANSI output parser for TunnelShell.

Parses and processes ANSI escape sequences in terminal output.
"""

import re
from dataclasses import dataclass
from typing import Optional, List, Tuple


@dataclass
class AnsiCode:
    """Represents an ANSI escape code."""
    raw: str
    code_type: str  # 'csi', 'osc', 'sgr'
    params: Optional[str] = None
    command: Optional[str] = None


class AnsiParser:
    """Parses ANSI escape sequences from terminal output."""
    
    # CSI (Control Sequence Introducer) patterns
    CSI_PATTERN = re.compile(r'\x1b\[([0-9;]*)([A-Za-z])')
    
    # OSC (Operating System Command) patterns
    OSC_PATTERN = re.compile(r'\x1b\]([0-9]+);([^\x07\x1b]*)(?:\x07|\x1b\\)')
    
    # SGR (Select Graphic Rendition) codes
    SGR_CODES = {
        '0': 'reset',
        '1': 'bold',
        '2': 'dim',
        '3': 'italic',
        '4': 'underline',
        '5': 'blink',
        '7': 'reverse',
        '8': 'hidden',
        '22': 'normal_intensity',
        '23': 'not_italic',
        '24': 'not_underline',
        '25': 'not_blink',
        '27': 'not_reverse',
        '28': 'not_hidden',
        '30': 'fg_black',
        '31': 'fg_red',
        '32': 'fg_green',
        '33': 'fg_yellow',
        '34': 'fg_blue',
        '35': 'fg_magenta',
        '36': 'fg_cyan',
        '37': 'fg_white',
        '39': 'fg_default',
        '40': 'bg_black',
        '41': 'bg_red',
        '42': 'bg_green',
        '43': 'bg_yellow',
        '44': 'bg_blue',
        '45': 'bg_magenta',
        '46': 'bg_cyan',
        '47': 'bg_white',
        '49': 'bg_default',
    }
    
    # Common CSI commands
    CSI_COMMANDS = {
        'A': 'cursor_up',
        'B': 'cursor_down',
        'C': 'cursor_forward',
        'D': 'cursor_back',
        'E': 'cursor_next_line',
        'F': 'cursor_prev_line',
        'G': 'cursor_horizontal_absolute',
        'H': 'cursor_position',
        'J': 'erase_display',
        'K': 'erase_line',
        'L': 'insert_lines',
        'M': 'delete_lines',
        'P': 'delete_characters',
        'S': 'scroll_up',
        'T': 'scroll_down',
        'm': 'sgr',  # Select Graphic Rendition
        'n': 'device_status',
        's': 'save_cursor',
        'u': 'restore_cursor',
        '?': 'private_mode',
    }
    
    def parse(self, text: str) -> Tuple[str, List[AnsiCode]]:
        """Parse ANSI codes from text.
        
        Returns (clean_text, list_of_codes).
        """
        codes = []
        
        # Find all CSI sequences
        for match in self.CSI_PATTERN.finditer(text):
            params = match.group(1)
            command = match.group(2)
            codes.append(AnsiCode(
                raw=match.group(0),
                code_type='csi',
                params=params,
                command=command,
            ))
        
        # Find all OSC sequences
        for match in self.OSC_PATTERN.finditer(text):
            codes.append(AnsiCode(
                raw=match.group(0),
                code_type='osc',
                params=match.group(1),
                command=match.group(2),
            ))
        
        # Remove ANSI codes from text
        clean_text = self.strip(text)
        
        return clean_text, codes
    
    def strip(self, text: str) -> str:
        """Remove all ANSI escape sequences from text."""
        # Remove CSI sequences
        text = self.CSI_PATTERN.sub('', text)
        # Remove OSC sequences
        text = self.OSC_PATTERN.sub('', text)
        # Remove other common escape sequences
        text = re.sub(r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)', '', text)
        text = re.sub(r'\x1b[()][AB012]', '', text)  # Character set
        text = re.sub(r'\x1b[=>]', '', text)  # Keypad mode
        text = re.sub(r'\x1b[78]', '', text)  # Save/restore cursor
        text = re.sub(r'\x1b\[\\?[\d;]*[A-Za-z]', '', text)  # Generic CSI
        return text
    
    def parse_sgr(self, params: str) -> List[str]:
        """Parse SGR (Select Graphic Rendition) parameters.
        
        Returns list of style names.
        """
        if not params:
            return ['reset']
        
        styles = []
        for code in params.split(';'):
            if code in self.SGR_CODES:
                styles.append(self.SGR_CODES[code])
            elif code.startswith('38;') or code.startswith('48;'):
                # Extended color (256 or RGB)
                parts = code.split(';')
                if len(parts) >= 3:
                    if parts[1] == '5':  # 256 color
                        styles.append(f'color256_{parts[2]}')
                    elif parts[1] == '2':  # RGB
                        styles.append(f'rgb_{parts[2]}_{parts[3]}_{parts[4]}')
        
        return styles
    
    def get_cursor_movement(self, code: AnsiCode) -> Optional[Tuple[str, int]]:
        """Get cursor movement from CSI code.
        
        Returns (direction, count) or None.
        """
        if code.code_type != 'csi':
            return None
        
        if code.command not in ('A', 'B', 'C', 'D'):
            return None
        
        direction = {
            'A': 'up',
            'B': 'down',
            'C': 'forward',
            'D': 'back',
        }.get(code.command)
        
        count = int(code.params) if code.params else 1
        
        return (direction, count)
    
    def is_clear_screen(self, code: AnsiCode) -> bool:
        """Check if code clears the screen."""
        return (
            code.code_type == 'csi' and
            code.command == 'J' and
            code.params in ('', '0', '2', '3')
        )
    
    def is_clear_line(self, code: AnsiCode) -> bool:
        """Check if code clears the line."""
        return (
            code.code_type == 'csi' and
            code.command == 'K'
        )


# Global parser instance
_parser = AnsiParser()


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape sequences from text."""
    return _parser.strip(text)


def parse_ansi(text: str) -> Tuple[str, List[AnsiCode]]:
    """Parse ANSI codes from text."""
    return _parser.parse(text)