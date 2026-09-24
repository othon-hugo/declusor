# Core Package

The **core** package provides infrastructure services implementing domain contracts defined in the `contract` package.

## Modules

| Module              | Class            | Implements                                                                                                               |
| ------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `router.py`         | `Router`         | `IRouter` — route-table management, controller lookup, and usage text                                                    |
| `parser.py`         | `DeclusorParser` | `IParser[DeclusorOptions]` — command-line option parser with dynamic client discovery                                    |
| `plugin_manager.py` | `PluginManager`  | Multi-tier plugin discovery engine (built-in directories, entry points, drop-in folders) with strict contract validation |
| `clients.py`        | `ClientRegistry` | Base registry mapping client identifiers to their plugin classes                                                         |

> [!NOTE]
> Interactive terminal components (console I/O and prompt loops) live in `presentation`. Concrete client plugins live in the external `plugins/` directory and third-party packages.

## Design Principles

1. **Contract Compliance** — classes implement abstractions defined in `contract`.
2. **Infrastructure Decoupling** — routing and parsing are completely decoupled from concrete client implementations.
3. **Multi-Tier Discovery & Precedence** — `PluginManager` discovers plugins dynamically at runtime across built-ins, PEP 621 entry points, and drop-in folders.
4. **Validation Barrier** — `PluginManager` validates plugin classes prior to registration, preventing faulty third-party code from compromising runtime stability.
