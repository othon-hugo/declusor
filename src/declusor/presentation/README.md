# Presentation Package

The **presentation** package implements the operator user interface and interactive REPL view loop for Declusor.

## Modules

| Module       | Class       | Implements                                                              |
| ------------ | ----------- | ----------------------------------------------------------------------- |
| `console.py` | `Console`   | `IConsole` — readline-backed terminal I/O with tab-completion & history |
| `prompt.py`  | `PromptCLI` | `IPrompt` — interactive read-eval-dispatch loop with SessionContext     |

## Design Principles

1. **View Layer Separation** — handles operator display and input formatting without business or network transport logic.
2. **Signal-Driven Loop** — responds to `ControllerResult` and `ControllerAction` lifecycle signals without relying on control-flow exceptions.
3. **Session-Context Binding** — passes the active `SessionContext` to routed controllers, enabling direct command execution.
