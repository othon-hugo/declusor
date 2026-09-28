# Command Package

The **command** package implements the Command design pattern. Each class encapsulates one remote operation and its data-formatting logic.

## Modules

| Module            | Responsibility                                          |
| ----------------- | ------------------------------------------------------- |
| `_base`           | Base streaming command abstraction for chunked I/O      |
| `execute_code`    | Encode and transmit native client runtime code          |
| `execute_command` | Encode and transmit a shell command                     |
| `execute_file`    | Encode a local file and invoke a client operation       |
| `upload_file`     | Encode a local file and invoke a client operation       |
| `load_module`     | Load an operator-selected module from client file store |
| `launch_shell`    | Manage an interactive shell session                     |

## Design Principles

1. **Single Responsibility**: each command performs one operation.
2. **Interface Compliance**: commands implement `ICommand` and depend on `IConnection`, `IView`, and `IInputSource`.
3. **Stateless Execution**: commands receive session state through `execute`.
4. **Synchronous I/O**: `LaunchShell` uses `TaskPool` for bidirectional shell traffic.
