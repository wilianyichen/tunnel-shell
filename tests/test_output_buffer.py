"""Tests for OutputBuffer class."""

import pytest
from tunnelshell.output_buffer import OutputBuffer


class TestAppendAndGetLines:
    """Tests for append and get_lines functionality."""

    def test_append_single_line(self):
        """Test appending a single line."""
        buffer = OutputBuffer()
        buffer.append("Hello World")
        
        result = buffer.get_recent(1)
        assert result == "Hello World"

    def test_append_multiple_lines(self):
        """Test appending multiple lines."""
        buffer = OutputBuffer()
        buffer.append("Line 1\nLine 2\nLine 3")
        
        result = buffer.get_recent(10)
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result

    def test_get_recent_lines(self):
        """Test getting recent N lines."""
        buffer = OutputBuffer()
        for i in range(10):
            buffer.append(f"Line {i}")
        
        result = buffer.get_recent(3)
        lines = result.split("\n")
        assert len(lines) == 3
        assert "Line 7" in result
        assert "Line 8" in result
        assert "Line 9" in result

    def test_get_all_lines(self):
        """Test getting all lines."""
        buffer = OutputBuffer()
        buffer.append("Line A")
        buffer.append("Line B")
        buffer.append("Line C")
        
        result = buffer.get_all()
        assert "Line A" in result
        assert "Line B" in result
        assert "Line C" in result


class TestBufferLimit:
    """Tests for buffer limit functionality."""

    def test_buffer_trims_when_exceeds_max_bytes(self):
        """Test that buffer trims when exceeding max_bytes."""
        buffer = OutputBuffer(max_bytes=100)
        
        # Add data that exceeds the limit
        buffer.append("A" * 50)
        buffer.append("B" * 50)
        buffer.append("C" * 50)
        
        # Buffer should have trimmed some data
        stats = buffer.get_stats()
        assert stats["bytes"] <= 100


class TestClear:
    """Tests for clear functionality."""

    def test_clear_empty_buffer(self):
        """Test clearing an empty buffer."""
        buffer = OutputBuffer()
        buffer.clear()
        
        result = buffer.get_all()
        assert result == ""

    def test_clear_buffer_with_data(self):
        """Test clearing a buffer with data."""
        buffer = OutputBuffer()
        buffer.append("Line 1")
        buffer.append("Line 2")
        buffer.append("Line 3")
        
        buffer.clear()
        
        result = buffer.get_all()
        assert result == ""
        
        stats = buffer.get_stats()
        assert stats["lines"] == 0
        assert stats["bytes"] == 0

    def test_clear_and_reuse(self):
        """Test clearing and reusing the buffer."""
        buffer = OutputBuffer()
        buffer.append("Old data")
        buffer.clear()
        buffer.append("New data")
        
        result = buffer.get_all()
        assert result == "New data"
        assert "Old" not in result


class TestStripAnsi:
    """Tests for strip_ansi functionality."""

    def test_strip_ansi_color_codes(self):
        """Test stripping ANSI color codes."""
        text = "\x1b[31mRed Text\x1b[0m"
        result = OutputBuffer.strip_ansi(text)
        assert result == "Red Text"

    def test_strip_ansi_multiple_codes(self):
        """Test stripping multiple ANSI codes."""
        text = "\x1b[1;32;40mBold Green on Black\x1b[0m"
        result = OutputBuffer.strip_ansi(text)
        assert result == "Bold Green on Black"

    def test_strip_ansi_cursor_codes(self):
        """Test stripping ANSI cursor codes."""
        text = "\x1b[2J\x1b[HClear Screen"
        result = OutputBuffer.strip_ansi(text)
        assert result == "Clear Screen"

    def test_strip_ansi_no_codes(self):
        """Test text without ANSI codes remains unchanged."""
        text = "Plain text without codes"
        result = OutputBuffer.strip_ansi(text)
        assert result == text

    def test_strip_ansi_empty_string(self):
        """Test stripping ANSI from empty string."""
        result = OutputBuffer.strip_ansi("")
        assert result == ""


class TestEmptyBuffer:
    """Tests for empty buffer behavior."""

    def test_get_recent_from_empty_buffer(self):
        """Test getting recent lines from empty buffer."""
        buffer = OutputBuffer()
        result = buffer.get_recent(10)
        assert result == ""

    def test_get_all_from_empty_buffer(self):
        """Test getting all lines from empty buffer."""
        buffer = OutputBuffer()
        result = buffer.get_all()
        assert result == ""

    def test_stats_for_empty_buffer(self):
        """Test stats for empty buffer."""
        buffer = OutputBuffer()
        stats = buffer.get_stats()
        
        assert stats["lines"] == 0
        assert stats["bytes"] == 0
        assert stats["max_lines"] == 1000
        assert stats["max_bytes"] == 1024 * 1024

    def test_append_empty_string(self):
        """Test appending empty string."""
        buffer = OutputBuffer()
        buffer.append("")
        
        stats = buffer.get_stats()
        assert stats["lines"] == 0
