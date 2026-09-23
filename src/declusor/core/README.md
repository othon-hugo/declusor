# Core Package

The **core** package provides infrastructure services implementing domain contracts defined in the `contract` package.

## Modules

| Module       | Class                      | Implements                                                            |
| ------------ | -------------------------- | --------------------------------------------------------------------- |
| `router.py`  | `Router`                   | `IRouter` — route-table management, controller lookup, and usage text |
| `parser.py`  | `DeclusorParser`           | `IParser[DeclusorOptions]` — command-line option parser               |
| `clients.py` | `ClientRegistry`, `Plugin` | Plugin registry for client transports and runtimes                    |

> [!NOTE]
> Interactive terminal components (console I/O and prompt loops) live in the `presentation` package. Transport state machines live in `connection`.

## Design Principles

1. **Contract Compliance** — classes implement abstractions defined in `contract`.
2. **Infrastructure Decoupling** — routing and parsing are decoupled from specific transport or presentation mechanics.
3. **Registry Isolation** — client registries support dependency injection for clean testing.
