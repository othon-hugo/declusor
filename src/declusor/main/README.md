# Main Package

The **main** package serves as the composition root and CLI entry point for the Declusor application.

> [!NOTE]
> This package integrates domain contracts, core infrastructure, controllers, and presentation layers into the runnable application.

## Modules

| Module     | Responsibility                                                                                     |
| ---------- | -------------------------------------------------------------------------------------------------- |
| `main`     | Application composition root, CLI dispatching, execution mode resolution, and process exit mapping |
| `terminal` | Specialized interactive terminal application bootstrap runner (`run_terminal_app`)                 |

## Design Principles

1. **Composition Root** — wires concrete dependencies and registries; `core.Application` composes official routes with the selected plugin's route table.
2. **Defensive Lifecycle** — orchestrates clean transitions from socket listening to connection initialization and session runner execution.
3. **Structured Exit Codes** — catches domain exceptions and maps them to deterministic process exit codes (`0` for success/interrupt, `1` for general errors, `2` for parser errors).
4. **Decoupled Architecture** — depends on abstractions and delegates execution to specialized layers without leaking implementation details.
5. **Headless & Agent Orchestration** — provides fine-grained dependency injection for headless testing, in-memory transport registries, custom diagnostic streams, and programmatic agent orchestration.
