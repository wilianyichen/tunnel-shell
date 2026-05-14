# API Reference

Complete API documentation for TunnelShell.

## Table of Contents

- [Configuration](#configuration)
- [Connection](#connection)
- [Session](#session)
- [File Transfer](#file-transfer)
- [Port Forwarding](#port-forwarding)
- [Exceptions](#exceptions)

---

## Configuration

### SSHConfig

SSH connection configuration.

```python
from tunnelshell.config import SSHConfig

config = SSHConfig(
    host="example.com",      # Required: hostname or IP
    port=22,                 # Optional: SSH port (default: 22)
    user="myuser",           # Optional: username
    key_filename="~/.ssh/id_rsa",  # Optional: SSH key path
    timeout=30,              # Optional: connection timeout
)
```

#### Methods

**`from_host_alias(host: str) -> SSHConfig`**

Create config from SSH config alias.

```python
config = SSHConfig.from_host_alias("myserver")
```

---

## Connection

### Connection

Synchronous SSH connection.

```python
from tunnelshell.connection import Connection

conn = Connection(config)
conn.connect()
output, exit_code = conn.execute("ls -la")
conn.disconnect()
```

#### Methods

**`connect() -> None`**

Establish SSH connection.

**`execute(command: str, timeout: int = 30) -> Tuple[str, int]`**

Execute command and return (output, exit_code).

**`disconnect() -> None`**

Close connection.

---

## Session

### PTYSession

Persistent PTY session.

```python
from tunnelshell.session import PTYSession

session = PTYSession(
    session_id="my-session",
    config=config,
    name="deploy"
)
session.create()
session.send_line("ls -la")
output = session.read_output()
session.detach()
```

#### Methods

**`create() -> None`** - Create session
**`send_line(line: str) -> None`** - Send command
**`read_output(timeout: float = 1.0) -> str`** - Read output
**`detach() -> None`** - Detach (keep running)
**`kill() -> None`** - Kill session

---

## File Transfer

### FileTransfer

SFTP file operations.

```python
from tunnelshell.file_transfer import FileTransfer

transfer = FileTransfer(connection)
transfer.upload("local.txt", "/remote/path.txt")
transfer.download("/remote/file.txt", "local.txt")
files = transfer.list_dir("/home/user")
```

#### Methods

**`upload(local_path: str, remote_path: str) -> bool`**
**`download(remote_path: str, local_path: str) -> bool`**
**`list_dir(remote_path: str) -> List[str]`**

---

## Port Forwarding

### ForwardManager

Manage port forwards.

```python
from tunnelshell.port_forward import ForwardManager

manager = ForwardManager(transport)

# Local forward: localhost:8080 -> remote:80
manager.add_local_forward(8080, "localhost", 80)

# Remote forward: remote:8080 -> localhost:3000
manager.add_remote_forward(8080, "localhost", 3000)

manager.start_forward("local_8080_localhost_80")
manager.list_forwards()
manager.stop_all()
```

---

## Exceptions

### Exception Hierarchy

```python
from tunnelshell.exceptions import (
    TunnelShellError,      # Base exception
    ConnectionError,       # Connection errors
    AuthenticationError,   # Auth failed
    SessionError,          # Session errors
    CommandError,          # Command errors
    TransferError,         # File transfer errors
)
```

### Usage

```python
try:
    conn.connect()
except AuthenticationError as e:
    print(f"Error: {e.message}")
    print(f"Suggestion: {e.suggestion}")
```

---

## Retry Mechanism

### retry decorator

```python
from tunnelshell.retry import retry

@retry(max_attempts=3, delay=1.0, backoff='exponential')
def connect_with_retry():
    conn.connect()
```

### RetryConfig

```python
from tunnelshell.retry import RetryConfig, retry_call

config = RetryConfig(
    max_attempts=5,
    delay=2.0,
    backoff='linear',
    exceptions=(ConnectionError,)
)

retry_call(conn.connect, config=config)
```

---

## Connection Pool

### ConnectionPool

```python
from tunnelshell.pool import ConnectionPool

pool = ConnectionPool(max_connections=10)

# Context manager
async with pool.connection(config) as conn:
    await conn.execute("hostname")

# Manual
conn = await pool.get(config)
try:
    await conn.execute("ls")
finally:
    await pool.release(config, conn)
```

---

## Interactive Terminal

### InteractiveTerminal

```python
from tunnelshell.interactive import InteractiveTerminal

terminal = InteractiveTerminal(host="myserver")
terminal.spawn()
terminal.send("ls -la\n")
output = terminal.read()
terminal.kill()
```

---

## Async Support

### AsyncConnection

```python
from tunnelshell.async_connection import AsyncConnection

async def main():
    conn = AsyncConnection(config)
    await conn.connect()
    exit_code, stdout, stderr = await conn.execute("hostname")
    await conn.disconnect()
```

### AsyncPTYSession

```python
from tunnelshell.async_session import AsyncPTYSession

async def main():
    session = AsyncPTYSession(session_id="test", config=config)
    await session.create()
    await session.send_line("ls")
    output = await session.read_output()
    await session.kill()
```
