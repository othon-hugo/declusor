# Presentation Package

The **presentation** package implements the operator user interface and interactive REPL view loop for Declusor.

## Modules

| Module         | Responsibility                                                                                         |
| -------------- | ------------------------------------------------------------------------------------------------------ |
| `input_source` | Terminal input reading via readline with history and autocompletion (`TerminalInputSource`)            |
| `prompt`       | Interactive command loop and session runner (`PromptLoop` implements `ISessionRunner`)                 |
| `request`      | Concrete command request parser implementation bridging input lines with schemas (`ControllerRequest`) |
| `view`         | Standard output streams, binary data flushing, and semantic levels (`TerminalView`)                    |

## Design Principles

1. **View Layer Separation** — handles operator display and input formatting without business or network transport logic.
2. **Signal-Driven Loop** — responds to `ControllerResult` and `ControllerAction` lifecycle signals without relying on control-flow exceptions.
3. **Session-Context Binding** — passes the active `SessionContext` to routed controllers, enabling direct command execution.
4. **Command-Aware Autocompletion** — `TerminalInputSource.setup_completer` accepts an optional `assets_dir` parameter, scoping `load` autocompletion directly to the active plugin's payload modules (`assets/modules/`) while preserving host filesystem navigation (`.` or explicit `./`, `/`) for host-directed operations (`upload`, `execute`), automatically filtering out common non-essential artifacts (`__pycache__`, `.git`, `.venv`, `.pyc`, etc.) via configurable blocklists.
