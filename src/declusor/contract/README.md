# Contract Package (Domain Layer)

The **contract** package defines the abstract contracts that establish the boundaries between system components. This is the **domain layer** — pure abstractions and lifecycle state machines with no framework implementation logic.

> [!NOTE]
> This package depends only on foundation layers (`config` and `util`). It has zero dependencies on concrete implementation packages (`core`, `command`, `controller`, `presentation`, `main`, or external `plugins`).

## Modules

| Module       | Responsibility                                                                |
| ------------ | ----------------------------------------------------------------------------- |
| `client`     | Abstractions for client plugins, runtimes, and client file stores             |
| `command`    | Execution lifecycle contract for encapsulated command operations              |
| `connection` | State machine contract and protocol profile interfaces for network transports |
| `console`    | Terminal input and output presentation contract                               |
| `controller` | Controller signatures, request/result types, and `SessionContext` coordinator |
| `parser`     | Interface for CLI argument parsing and options mapping                        |
| `prompt`     | Contract for interactive terminal REPL execution loops                        |
| `router`     | Route registration, lookup, and documentation contract                        |

## Design Principles

1. **Pure Abstractions** — interfaces contain only `@abstractmethod` signatures, invariant state machines, and docstrings.
2. **Single Responsibility** — each contract defines exactly one concern.
3. **Rigid Interface / Extensible Implementation** — client plugins implemented in the external `plugins/` hierarchy or third-party packages strictly adhere to `IClientPlugin` and `IConnection`.
4. **Liskov Substitution** — any plugin conforming to `IClientPlugin` is drop-in replaceable and discoverable at runtime.
