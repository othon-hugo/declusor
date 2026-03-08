# Controller Package

The **controller** package is the application layer — thin functions that parse user input, delegate to command objects, and present output.

## Modules

| Module       | Function                 | Command                                                       |
| ------------ | ------------------------ | ------------------------------------------------------------- |
| `command.py` | `call_command`           | Execute a single shell command on the remote system           |
| `execute.py` | `call_execute`           | Execute a local script on the remote system                   |
| `exit.py`    | `call_exit`              | Raise `ExitRequest` to terminate the session                  |
| `help.py`    | `create_help_controller` | Factory returning a closure that displays route documentation |
| `load.py`    | `call_load`              | Load and run a local payload on the remote system             |
| `shell.py`   | `call_shell`             | Open an interactive shell session                             |
| `upload.py`  | `call_upload`            | Upload a local file to the remote system                      |

## Controller Signature

All controllers follow the `MetaController` type alias:

```python
def call_*(connection: IConnection, console: IConsole, line: str) -> None
```

## Lifecycle

1. Receive `(connection, console, line)` from the router.
2. Parse and validate `line` via `parse_command_arguments`.
3. Perform pre-execution checks (e.g. `ensure_file_exists`).
4. Instantiate and execute the appropriate `ICommand`.
5. Forward response output to `console`.

## Design Principles

1. **Thin Controllers** — business logic lives in `command` objects and `util` functions.
2. **Dependency Injection** — controllers depend on `IConnection` / `IConsole`, not concrete types.
3. **Error Propagation** — domain exceptions propagate to the prompt loop for centralised handling.
