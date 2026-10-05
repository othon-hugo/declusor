# Contract Package (Domain Layer)

The **contract** package defines the abstract contracts that establish the boundaries between system components. This is the **domain layer** — pure abstractions and lifecycle state machines with no framework implementation logic.

> [!NOTE]
> This package depends only on the foundation base (`config`). It has zero dependencies on `util`, `core`, `command`, `controller`, `presentation`, `main`, or external `plugins`.

## Modules

| Module         | Responsibility                                                                                      |
| -------------- | --------------------------------------------------------------------------------------------------- |
| `command`      | Execution lifecycle contract for encapsulated command operations                                    |
| `connection`   | State machine contract and protocol profile interfaces for network transports                       |
| `controller`   | Controller signatures, request/result types, and `SessionContext` coordinator                       |
| `input_source` | Operator input reading contract (command and raw lines)                                             |
| `parser`       | Interface for CLI argument parsing and options mapping                                              |
| `plugin`       | Abstractions for client plugins, declared controller capabilities, runtimes, and client file stores |
| `router`       | Route registration, lookup, and usage contract                                                      |
| `runner`       | Session workflow and interaction loop contract (`ISessionRunner`)                                   |
| `transport`    | Bidirectional byte-stream transport channel and transport listener contracts                        |
| `view`         | Output presentation contract for messages, errors, warnings, info, and binary                       |

## Design Principles

1. **Pure Abstractions** — interfaces contain only `@abstractmethod` signatures, invariant state machines, and docstrings.
2. **Single Responsibility** — each contract defines exactly one concern.
3. **Rigid Interface / Extensible Implementation** — client plugins implemented in the external `plugins/` hierarchy or third-party packages strictly adhere to `IPlugin` and `IConnection`.
4. **Liskov Substitution** — any plugin conforming to `IPlugin` is drop-in replaceable and discoverable at runtime.

`IPluginExtension.supported_controllers` is a required immutable set of `config.ControllerType` values. It advertises the plugin-specific routes available to its runtime; universal `help` and `exit` routes are supplied by the application.
