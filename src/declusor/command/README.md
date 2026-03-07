# Command Package

The **command** package implements the Command design pattern — each class encapsulates a single remote operation and its data-formatting logic.

## Modules

| Module       | Class                       | Responsibility                                                    |
| ------------ | --------------------------- | ----------------------------------------------------------------- |
| `execute.py` | `ExecuteCommand`            | UTF-8 encode a shell command and transmit it                      |
| `file.py`    | `ExecuteFile`, `UploadFile` | Base64-encode a local file and transmit it with an operation code |
| `load.py`    | `LoadPayload`               | Read a local payload script and transmit the raw bytes            |
| `shell.py`   | `LaunchShell`               | Spawn request/response threads for an interactive shell session   |

## Design Principles

1. **Single Responsibility** — each command performs exactly one operation.
2. **Interface Compliance** — all commands implement `ICommand` and depend on `IConnection` / `IConsole`.
3. **Stateless Execution** — commands receive all state through constructors and `execute` parameters.
4. **Synchronous I/O** — no async; `LaunchShell` uses `TaskPool` threads for concurrency.
