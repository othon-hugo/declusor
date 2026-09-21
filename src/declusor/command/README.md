# Command Package

The **command** package implements the Command design pattern. Each class
encapsulates one remote operation and its data-formatting logic.

## Modules

| Module       | Class                       | Responsibility                                       |
| ------------ | --------------------------- | ---------------------------------------------------- |
| `execute.py` | `ExecuteCommand`            | Encode and transmit a shell command                  |
| `file.py`    | `ExecuteFile`, `UploadFile` | Encode a local file and invoke a client operation    |
| `load.py`    | `LoadModule`                | Load an operator-selected module from `data/modules` |
| `shell.py`   | `LaunchShell`               | Manage an interactive shell session                  |

## Design Principles

1. **Single Responsibility**: each command performs one operation.
2. **Interface Compliance**: commands implement `ICommand` and depend on `IConnection` and `IConsole`.
3. **Stateless Execution**: commands receive session state through `execute`.
4. **Synchronous I/O**: `LaunchShell` uses `TaskPool` for bidirectional shell traffic.
