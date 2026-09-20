# Presentation Package

The **presentation** package implements the operator user interface and interactive REPL view loop for Declusor.

## Modules

| Module         | Responsibility                                                                              |
| -------------- | ------------------------------------------------------------------------------------------- |
| `input_source` | Terminal input reading via readline with history and autocompletion (`TerminalInputSource`) |
| `prompt`       | Interactive command loop and session runner (`PromptLoop` implements `ISessionRunner`)      |
| `view`         | Standard output streams, binary data flushing, and semantic levels (`TerminalView`)         |

## Design Principles

1. **View Layer Separation** — handles operator display and input formatting without business or network transport logic.
2. **Signal-Driven Loop** — responds to `ControllerResult` and `ControllerAction` lifecycle signals without relying on control-flow exceptions.
3. **Session-Context Binding** — passes the active `SessionContext` to routed controllers, enabling direct command execution.
