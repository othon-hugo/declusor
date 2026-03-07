# Core Package

The **core** package provides the concrete runtime implementations of the domain interfaces defined in the `interface` package.

## Modules

| Module       | Class       | Implements                                                                                             |
| ------------ | ----------- | ------------------------------------------------------------------------------------------------------ |
| `console.py` | `Console`   | `IConsole` — readline-backed terminal I/O with tab-completion and history                              |
| `parser.py`  | `Parser`    | `IParser` — `argparse.ArgumentParser` subclass that raises `ParserError` instead of calling `sys.exit` |
| `prompt.py`  | `PromptCLI` | `IPrompt` — the main read-eval-dispatch loop                                                           |
| `router.py`  | `Router`    | `IRouter` — route-table management, controller lookup, and help-text generation                        |

> [!NOTE]
> Session management (socket I/O, ACK framing) lives in the `connection` package, not here.

## Design Principles

1. **Interface Compliance** — every class in this package implements an `interface` contract.
2. **Synchronous Architecture** — all I/O is blocking; no async primitives.
3. **Separation of Concerns** — console, routing, parsing, and prompting are independent.
4. **Extensibility** — new console backends or router strategies can be added via the interface layer.
