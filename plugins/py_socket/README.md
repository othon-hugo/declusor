# Python Socket Plugin (`py_socket`)

The `py_socket` plugin provides a cross-platform Python-based reverse-shell client capable of executing payloads directly in-memory or delegating to the operating system shell.

## Modules

| Module       | Responsibility                                                             |
| ------------ | -------------------------------------------------------------------------- |
| `connection` | Python socket connection transport, protocol profile, and asset file store |
| `plugin`     | Entry-point plugin class (`IClientPlugin`) and runtime orchestrator        |

## Design Principles

1. **Pure Python Architecture** — compatible across Linux, macOS, and Windows with standard library only.
2. **Dual-Mode Execution** — dispatches between in-memory `exec()` with persistent session scope and subprocess execution.
3. **Contract Conformance** — fully conforms to `IClientPlugin`, `IClientRuntime`, and `IConnection` interfaces.
4. **Resilient Transport** — provides framed communication with SHA-256 ACK validation and structured error translation.
