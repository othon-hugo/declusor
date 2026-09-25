# Core Package

The **core** package provides infrastructure services implementing domain contracts defined in the `contract` package.

> [!NOTE]
> Interactive terminal components (console I/O and prompt loops) live in `presentation`. Concrete client plugins live in the external `plugins/` directory and third-party packages.

## Modules

| Module   | Responsibility                                                                    |
| -------- | --------------------------------------------------------------------------------- |
| `parser` | CLI argument parsing, option normalization, and client registry binding           |
| `plugin` | Dynamic plugin discovery across tiers, contract validation, and client registries |
| `router` | Command routing, controller dispatching, and usage documentation mapping          |

## Design Principles

1. **Contract Compliance** — classes implement abstractions defined in `contract`.
2. **Infrastructure Decoupling** — routing and parsing are completely decoupled from concrete client implementations.
3. **Multi-Tier Discovery & Precedence** — `PluginManager` discovers plugins dynamically at runtime across built-ins, PEP 621 entry points, and drop-in folders.
4. **Validation Barrier** — `PluginManager` validates plugin classes prior to registration, preventing faulty third-party code from compromising runtime stability.
