# Contract Package (Domain Layer)

The **contract** package defines the abstract contracts that establish the boundaries between system components. This is the **domain layer** — pure abstractions and lifecycle state machines with no framework implementation logic.

> [!NOTE]
> This package depends only on the foundation base (`config`). It has zero dependencies on `util`, `core`, `command`, `controller`, `presentation`, `main`, or external `plugins`.

## Modules

| Module         | Responsibility                                                                    |
| -------------- | --------------------------------------------------------------------------------- |
| `command`      | Execution lifecycle contract for encapsulated command operations                  |
| `connection`   | State machine contract and protocol profile interfaces for network transports     |
| `controller`   | Controller signatures and request/result types                                    |
| `input_source` | Operator input reading contract (command and raw lines)                           |
| `parser`       | Interface for CLI argument parsing and options mapping                            |
| `plugin`       | Abstractions for client plugins, route tables, runtimes, and client file stores   |
| `router`       | Route registration, lookup, and usage contract                                    |
| `session`      | Active session context and workflow contract (`SessionContext`, `ISessionRunner`) |
| `transport`    | Bidirectional byte-stream transport channel and transport listener contracts      |
| `view`         | Output presentation contract for messages, errors, warnings, info, and binary     |

## Design Principles

1. **Pure Abstractions** — interfaces contain only `@abstractmethod` signatures, invariant state machines, and docstrings.
2. **Single Responsibility** — each contract defines exactly one concern.
3. **Rigid Interface / Extensible Implementation** — client plugins implemented in the external `plugins/` hierarchy or third-party packages strictly adhere to `IPluginExtension` and `IConnection`.
4. **Liskov Substitution** — any plugin conforming to `IPluginExtension` is drop-in replaceable and discoverable at runtime.

`IPluginExtension.routes` is a mapping from arbitrary route-name strings to `RouteRegistration` values. It allows plugins to add routes and replace official registrations during application composition. The application owns protected `help` and `exit` routes.
