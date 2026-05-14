"""Tests for TunnelShell CLI."""

import subprocess
import sys


def test_version() -> None:
    """Test that --version works."""
    result = subprocess.run(
        [sys.executable, "-m", "tunnelshell.cli", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "0.1.0" in result.stdout


def test_help() -> None:
    """Test that --help works."""
    result = subprocess.run(
        [sys.executable, "-m", "tunnelshell.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "TunnelShell" in result.stdout