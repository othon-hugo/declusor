# Connection Package

The **connection** package provides the concrete `IConnection` + `IProfile` implementation that drives Declusor's TCP socket-based protocol.

## Modules

| Module            | Class                   | Responsibility                                                                                                             |
| ----------------- | ----------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `shell_socket.py` | `ShellSocketProfile`    | Frozen dataclass holding host, port, ACK values, and operation-code → function-name mapping                                |
|                   | `ShellSocketConnection` | Manages a raw TCP socket with ACK-framed reading, blocking writes, library-upload handshake, and context-manager lifecycle |

## Protocol Details

- **ACK Framing** — every `read` scans for the client ACK marker to detect end-of-message.
- **Library Upload** — `initialize()` sends the shell library and validates the client ACK.
- **Timeout Management** — configurable per-read timeout; interactive shell sets timeout to `None`.

## Design Principles

1. **Interface Compliance** — `ShellSocketConnection` implements `IConnection`; `ShellSocketProfile` implements `IProfile`.
2. **Context Manager** — connection lifecycle is managed via `__enter__` / `__exit__`.
3. **Synchronous I/O** — all socket operations are blocking.
4. **Immutable Configuration** — `ShellSocketProfile` is a frozen `@dataclass`.
