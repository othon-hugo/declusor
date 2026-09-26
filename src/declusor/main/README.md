# Main Package

The **main** package serves as the composition root and CLI entry point for the Declusor application.

> [!NOTE]
> This package integrates domain contracts, core infrastructure, controllers, and presentation layers into the runnable application.

## Modules

| Module | Responsibility                                                                     |
| ------ | ---------------------------------------------------------------------------------- |
| `app`  | Application composition, route wiring, plugin registration, and execution flow     |
| `cli`  | CLI entry point function, process argument handling, and process exit code mapping |

## Design Principles

1. **Composition Root** — wires all concrete dependencies, routes, and registries in one top-level coordinator.
2. **Defensive Lifecycle** — orchestrates clean transitions from socket listening to connection initialization and session runner execution.
3. **Structured Exit Codes** — catches domain exceptions and maps them to deterministic process exit codes (`0` for success/interrupt, `1` for general errors, `2` for parser errors).
4. **Decoupled Architecture** — depends on abstractions and delegates execution to specialized layers without leaking implementation details.
