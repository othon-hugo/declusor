# Controller Package

The **controller** package is the application layer. Controllers parse user
input, delegate to command objects, and present output.

## Modules

| Module       | Function                 | Responsibility                                       |
| ------------ | ------------------------ | ---------------------------------------------------- |
| `command.py` | `call_command`           | Execute a shell command remotely                     |
| `execute.py` | `call_execute`           | Execute a local script remotely                      |
| `exit.py`    | `call_exit`              | Request session termination                          |
| `help.py`    | `create_help_controller` | Build the help controller                            |
| `load.py`    | `call_load`              | Load an operator-selected module from `data/modules` |
| `shell.py`   | `call_shell`             | Open an interactive shell session                    |
| `upload.py`  | `call_upload`            | Upload a local file remotely                         |

## Controller Signature

All controllers follow the `MetaController` type alias:

```python
def call_*(connection: IConnection, console: IConsole, req: contract.ControllerRequest) -> None
```

## Lifecycle

1. Receive `(session, console, line)` from the router.
2. Parse and validate `line`.
3. Instantiate and execute the appropriate `ICommand`.
4. Forward response output to `console`.

## Design Principles

1. **Thin Controllers**: business logic belongs in command objects.
2. **Dependency Injection**: controllers depend on interfaces, not concrete transports.
3. **Error Propagation**: domain exceptions propagate to the prompt loop.
