# TunnelShell Architecture Design

## Overview

TunnelShell is an agent-first remote terminal tool designed for AI agents to execute SSH operations programmatically. It provides persistent PTY sessions, file transfer, and structured output parsing.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Layer (cli.py)                      │
│  - Command parsing (Click)                                   │
│  - Output formatting (Rich)                                  │
│  - User interaction                                          │
├─────────────────────────────────────────────────────────────┤
│                    Session Layer (session.py)                │
│  - PTY session management                                    │
│  - Session persistence (session_store.py)                    │
│  - Output buffering (output_buffer.py)                       │
├─────────────────────────────────────────────────────────────┤
│                  Connection Layer (connection.py)            │
│  - SSH connection management                                 │
│  - Keep-alive handling                                       │
│  - Connection pooling (pool.py)                              │
├─────────────────────────────────────────────────────────────┤
│                   Transport Layer (paramiko)                 │
│  - SSH protocol implementation                               │
│  - Channel management                                        │
│  - SFTP operations                                           │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Configuration (config.py, config_manager.py)

**SSHConfig**: SSH connection configuration
- Host, port, user, key_filename
- Timeout settings
- Keep-alive parameters

**TunnelShellConfig**: Application configuration
- Server profiles
- Default settings
- Group management

### 2. Connection (connection.py, async_connection.py)

**Connection**: Synchronous SSH connection
- `connect()` - Establish connection
- `execute()` - Run command
- `disconnect()` - Close connection

**AsyncConnection**: Asynchronous SSH connection
- Uses asyncssh library
- Async/await interface
- Connection pooling support

### 3. Session (session.py, async_session.py)

**PTYSession**: Persistent PTY session
- Create, attach, detach, kill
- Output buffering
- Session persistence

**SessionStore**: Session persistence
- JSON file storage
- Cross-process session access

### 4. Output Processing

**OutputBuffer**: Output buffering
- Line-based storage
- ANSI stripping
- Size limits

**OutputParser**: ANSI parsing
- Color code extraction
- Cursor movement tracking

**PromptDetector**: Interactive prompt detection
- Password prompts
- Confirmation prompts
- Custom patterns

### 5. File Transfer (file_transfer.py)

**FileTransfer**: SFTP operations
- Upload, download
- Directory listing
- Progress tracking

### 6. Port Forwarding (port_forward.py)

**ForwardManager**: Port forwarding
- Local forward (local port → remote)
- Remote forward (remote port → local)
- Multiple forwards management

### 7. Security (security.py)

**SecurityChecker**: Command validation
- Dangerous command detection
- Whitelist/blacklist
- Risk assessment

### 8. Interactive Terminal (interactive.py)

**InteractiveTerminal**: Real interactive terminal
- PTY spawn
- Keyboard input
- Terminal resize

## Data Flow

### Command Execution Flow

```
User/Agent
    │
    ▼
CLI (cli.py)
    │ parse command
    ▼
Connection (connection.py)
    │ establish SSH
    ▼
Session (session.py)
    │ create PTY
    ▼
Execute Command
    │
    ▼
OutputBuffer (output_buffer.py)
    │ capture output
    ▼
OutputParser (output_parser.py)
    │ parse ANSI
    ▼
Return to CLI
    │ format with Rich
    ▼
User/Agent
```

### Session Persistence Flow

```
Create Session
    │
    ▼
PTYSession.create()
    │
    ▼
SessionStore.save()
    │ write to JSON
    ▼
~/.tunnelshell/sessions/sessions.json
    │
    │ (later)
    ▼
SessionStore.load()
    │ read from JSON
    ▼
PTYSession.attach()
    │ restore session
    ▼
Continue work
```

## Error Handling

### Exception Hierarchy

```
TunnelShellError (base)
├── ConnectionError
│   ├── AuthenticationError
│   ├── HostKeyError
│   └── ConnectionTimeoutError
├── SessionError
│   ├── SessionNotFoundError
│   ├── SessionTimeoutError
│   └── SessionNotRunningError
├── CommandError
│   ├── CommandTimeoutError
│   ├── CommandFailedError
│   └── CommandBlockedError
├── TransferError
│   ├── UploadError
│   ├── DownloadError
│   └── PathNotFoundError
└── ConfigError
    ├── HostNotFoundError
    └── InvalidConfigError
```

### Retry Mechanism

```python
from tunnelshell.retry import retry, RetryConfig

@retry(max_attempts=3, delay=1.0, backoff='exponential')
def connect_with_retry():
    connection.connect()
```

## Performance Optimization

### Connection Pooling

```python
from tunnelshell.pool import ConnectionPool

pool = ConnectionPool(max_connections=10)

async with pool.connection(config) as conn:
    await conn.execute("ls")
```

### Async Support

```python
from tunnelshell.async_connection import AsyncConnection

async def run_commands():
    conn = AsyncConnection(config)
    await conn.connect()
    result = await conn.execute("hostname")
    await conn.disconnect()
```

## Extension Points

### 1. Custom Output Handlers

```python
class CustomOutputHandler:
    def process(self, output: str) -> str:
        # Custom processing
        return output
```

### 2. Custom Security Rules

```python
class CustomSecurityChecker:
    def check(self, command: str) -> bool:
        # Custom validation
        return True
```

### 3. Custom Prompt Detectors

```python
class CustomPromptDetector:
    def detect(self, output: str) -> Optional[str]:
        # Custom detection
        return None
```

## File Structure

```
tunnel-shell/
├── src/tunnelshell/
│   ├── cli.py              # CLI commands
│   ├── config.py           # SSH config
│   ├── config_manager.py   # App config
│   ├── connection.py       # SSH connection
│   ├── async_connection.py # Async connection
│   ├── session.py          # PTY session
│   ├── async_session.py    # Async session
│   ├── session_store.py    # Session persistence
│   ├── output_buffer.py    # Output buffering
│   ├── output_parser.py    # ANSI parsing
│   ├── prompt_detector.py  # Prompt detection
│   ├── command_classifier.py # Command types
│   ├── file_transfer.py    # SFTP operations
│   ├── port_forward.py     # Port forwarding
│   ├── interactive.py      # Interactive terminal
│   ├── security.py         # Security checks
│   ├── timeout_manager.py  # Timeout handling
│   ├── recorder.py         # Session recording
│   ├── exceptions.py       # Exception classes
│   ├── retry.py            # Retry mechanism
│   └── pool.py             # Connection pool
├── tests/
│   ├── test_config.py
│   ├── test_connection.py
│   ├── test_session.py
│   └── test_output_buffer.py
├── docs/
│   ├── getting-started.md
│   ├── api-reference.md
│   └── examples.md
└── .github/workflows/
    └── test.yml
```

## Design Principles

1. **Agent-First**: Designed for programmatic use by AI agents
2. **Session Persistence**: Sessions survive across commands
3. **Structured Output**: Parseable, AI-friendly output format
4. **Error Recovery**: Comprehensive error handling and retry
5. **Security**: Built-in command validation
6. **Extensibility**: Plugin-friendly architecture