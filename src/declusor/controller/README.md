# Controller Package

The **controller** package is the application layer. Controllers parse user
input, delegate to command objects, and present output.

## Modules

| Module     | Responsibility                                       |
| ---------- | ---------------------------------------------------- |
| `command.` | Execute a shell command remotely                     |
| `execute.` | Execute a local script remotely                      |
| `exit.`    | Request session termination                          |
| `help.`    | Build the help controller                            |
| `load.`    | Load an operator-selected module from `data/modules` |
| `shell.`   | Open an interactive shell session                    |
| `upload.`  | Upload a local file remotely                         |

## Design Principles

1. **Thin Controllers**: business logic belongs in command objects.
2. **Dependency Injection**: controllers depend on interfaces, not concrete transports.
3. **Error Propagation**: domain exceptions propagate to the prompt loop.
