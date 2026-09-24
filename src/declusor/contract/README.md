# Contract Package (Domain Layer)

The **contract** package defines the abstract contracts that establish the boundaries between system components. This is the **domain layer** — pure abstractions and lifecycle state machines with no framework implementation logic.

> [!NOTE]
> This package depends only on foundation layers (`config` and `util`). It has zero dependencies on concrete implementation packages (`core`, `command`, `controller`, `presentation`, `main`, or external `plugins`).

## Modules & Contracts

| Module        | Responsability |
| ------------- | -------------- |
| `client`      |                |
| `connection.` |                |
| `command.`    |                |
| `controller.` |                |
| `console.`    |                |
| `parser.`     |                |
| `prompt.`     |                |
| `router.`     |                |

## Design Principles

1. **Pure Abstractions** — interfaces contain only `@abstractmethod` signatures, invariant state machines, and docstrings.
2. **Single Responsibility** — each contract defines exactly one concern.
3. **Rigid Interface / Extensible Implementation** — client plugins implemented in the external `plugins/` hierarchy or third-party packages strictly adhere to `IClientPlugin` and `IConnection`.
4. **Liskov Substitution** — any plugin conforming to `IClientPlugin` is drop-in replaceable and discoverable at runtime.
