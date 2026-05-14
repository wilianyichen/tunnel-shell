# TunnelShell

[![PyPI version](https://badge.fury.io/py/tunnel-shell.svg)](https://pypi.org/project/tunnel-shell/)
[![Python](https://img.shields.io/pypi/pyversions/tunnel-shell.svg)](https://pypi.org/project/tunnel-shell/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Agent-first remote terminal with persistent PTY sessions, file transfer, and AI-friendly output parsing.**

## Features

- **Persistent PTY Sessions** - Sessions survive across commands
- **File Transfer** - Upload, download, list files via SFTP
- **Port Forwarding** - Local and remote port forwarding
- **Interactive Terminal** - Real interactive terminal for vim, top, etc.
- **Structured Output** - Parseable, AI-friendly output format
- **Connection Pooling** - Reuse connections for better performance
- **Async Support** - Async/await interface for concurrent operations
- **Error Recovery** - Comprehensive error handling with retry mechanism
- **Security** - Built-in command validation and dangerous command detection

## Installation

```bash
# Basic installation
pip install tunnel-shell

# With async support
pip install "tunnel-shell[async]"

# With development tools
pip install "tunnel-shell[dev]"
```

## Quick Start

### Execute Single Command

```bash
tunnel-shell exec --host myserver --cmd 'hostname'
```

### Session Management

```bash
# Create session
tunnel-shell session create --host myserver --name deploy

# Execute commands in session
tunnel-shell session attach --name deploy --cmd 'ls -la'
tunnel-shell session attach --name deploy --cmd 'git status'

# List sessions
tunnel-shell session list

# Kill session
tunnel-shell session kill --name deploy
```

### File Transfer

```bash
# Upload
tunnel-shell file upload --host myserver --local file.txt --remote /tmp/file.txt

# Download
tunnel-shell file download --host myserver --remote /tmp/file.txt --local file.txt

# List directory
tunnel-shell file list --host myserver --path /home/user
```

### Port Forwarding

```bash
# Local port forward (access remote service locally)
tunnel-shell forward local --host myserver --local-port 8080 --remote-host localhost --remote-port 80

# Remote port forward (expose local service remotely)
tunnel-shell forward remote --host myserver --remote-port 8080 --local-host localhost --local-port 3000
```

### Interactive Terminal

```bash
# Start interactive session
tunnel-shell interactive --host myserver
```

## Configuration

### SSH Config

TunnelShell uses your existing SSH config (`~/.ssh/config`):

```
Host myserver
    HostName example.com
    Port 22
    User myuser
    IdentityFile ~/.ssh/id_rsa
```

### Application Config

Create `~/.tunnelshell/config.yaml`:

```yaml
servers:
  production:
    host: prod.example.com
    port: 22
    user: deploy
    tags:
      - production
    capabilities:
      - shell
      - file_transfer

defaults:
  timeout: 30
  connect_timeout: 10
```

## Python API

### Synchronous

```python
from tunnelshell.config import SSHConfig
from tunnelshell.connection import Connection

# Create config
config = SSHConfig(
    host="example.com",
    port=22,
    user="myuser"
)

# Connect and execute
conn = Connection(config)
conn.connect()
output, exit_code = conn.execute("ls -la")
conn.disconnect()
```

### Asynchronous

```python
import asyncio
from tunnelshell.config import SSHConfig
from tunnelshell.async_connection import AsyncConnection

async def main():
    config = SSHConfig(host="example.com", user="myuser")
    
    conn = AsyncConnection(config)
    await conn.connect()
    
    exit_code, stdout, stderr = await conn.execute("ls -la")
    
    await conn.disconnect()

asyncio.run(main())
```

### Connection Pooling

```python
from tunnelshell.pool import ConnectionPool, get_pool

async def run_commands():
    pool = ConnectionPool(max_connections=10)
    
    async with pool.connection(config) as conn:
        await conn.execute("hostname")
```

## Error Handling

```python
from tunnelshell.exceptions import (
    ConnectionError,
    AuthenticationError,
    CommandTimeoutError
)
from tunnelshell.retry import retry

@retry(max_attempts=3, delay=1.0)
def connect_with_retry():
    try:
        conn.connect()
    except AuthenticationError:
        print("Authentication failed")
    except ConnectionError as e:
        print(f"Connection error: {e.message}")
        print(f"Suggestion: {e.suggestion}")
```

## Documentation

- [Getting Started](docs/getting-started.md)
- [API Reference](docs/api-reference.md)
- [Examples](docs/examples.md)
- [Architecture](docs/architecture.md)

## Development

```bash
# Clone repository
git clone https://github.com/yourusername/tunnel-shell.git
cd tunnel-shell

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/tunnelshell
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [paramiko](https://www.paramiko.org/) - SSH library
- [asyncssh](https://github.com/ronf/asyncssh) - Async SSH library
- [Click](https://click.palletsprojects.com/) - CLI framework
- [Rich](https://github.com/Textualize/rich) - Terminal formatting