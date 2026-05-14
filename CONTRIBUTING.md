# Contributing to TunnelShell

Thank you for your interest in contributing to TunnelShell! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

Be respectful and inclusive. We welcome contributions from everyone.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip or poetry
- git

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/tunnel-shell.git
cd tunnel-shell

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install development dependencies
pip install -e ".[dev]"

# Install async support (optional)
pip install -e ".[async]"
```

### Run Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/tunnelshell

# Run specific test
pytest tests/test_connection.py -v
```

### Code Formatting

```bash
# Format code
black src/tunnelshell

# Sort imports
isort src/tunnelshell

# Type checking (optional)
mypy src/tunnelshell
```

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported
2. Create a new issue with:
   - Clear description
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment details

### Suggesting Features

1. Check if the feature has already been suggested
2. Create a new issue with:
   - Clear description
   - Use case
   - Proposed solution (optional)

### Contributing Code

1. Find an issue to work on
2. Comment on the issue to claim it
3. Fork and create a branch
4. Make your changes
5. Add tests
6. Submit a pull request

## Pull Request Process

1. **Create a branch**: `git checkout -b feature/your-feature-name`
2. **Make changes**: Follow coding standards
3. **Add tests**: Ensure all tests pass
4. **Update docs**: Update relevant documentation
5. **Commit**: Use clear commit messages
6. **Push**: `git push origin feature/your-feature-name`
7. **Create PR**: Fill out the PR template

### PR Checklist

- [ ] Code follows project style
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] All tests pass
- [ ] No merge conflicts

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints
- Write docstrings
- Keep functions small

### Example

```python
def execute_command(
    command: str,
    timeout: int = 30
) -> Tuple[str, int]:
    """
    Execute a command on remote server.

    Args:
        command: Command to execute
        timeout: Timeout in seconds

    Returns:
        Tuple of (output, exit_code)

    Raises:
        CommandTimeoutError: If command times out
    """
    # Implementation
    pass
```

### Imports

```python
# Standard library
import os
import sys
from typing import Optional, List

# Third-party
import paramiko
from rich.console import Console

# Local
from .config import SSHConfig
from .exceptions import CommandError
```

## Testing

### Test Structure

```
tests/
├── test_config.py        # Config tests
├── test_connection.py    # Connection tests
├── test_session.py       # Session tests
├── test_output_buffer.py # Output buffer tests
└── conftest.py           # Pytest fixtures
```

### Writing Tests

```python
import pytest
from tunnelshell.config import SSHConfig


class TestSSHConfig:
    """Tests for SSHConfig class."""

    def test_default_values(self):
        """Test default configuration values."""
        config = SSHConfig(host="example.com")
        assert config.host == "example.com"
        assert config.port == 22

    def test_custom_values(self):
        """Test custom configuration values."""
        config = SSHConfig(
            host="example.com",
            port=2222,
            user="testuser"
        )
        assert config.port == 2222
```

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_config.py

# Specific test
pytest tests/test_config.py::TestSSHConfig::test_default_values

# With coverage
pytest --cov=src/tunnelshell --cov-report=html
```

## Documentation

### Types of Documentation

1. **Code comments**: Explain complex logic
2. **Docstrings**: Document all public functions/classes
3. **README**: Getting started guide
4. **API docs**: Detailed API reference
5. **Examples**: Usage examples

### Docstring Format

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of function.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ExceptionType: When this exception is raised

    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        True
    """
    pass
```

## Release Process

1. Update version in `src/tunnelshell/version.py`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v0.x.x`
4. Push tag: `git push origin v0.x.x`
5. GitHub Actions will build and publish to PyPI

## Getting Help

- Open an issue for bugs/features
- Check existing documentation
- Review existing issues/PRs

Thank you for contributing!