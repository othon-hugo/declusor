# Core Package

The **core** package provides infrastructure services implementing domain contracts defined in the `contract` package.

> [!NOTE]
> Interactive terminal components (console I/O and prompt loops) live in `presentation`. Concrete client plugins live in the external `plugins/` directory and third-party packages.

## Modules

| Module        | Responsibility                                                                    |
| ------------- | --------------------------------------------------------------------------------- |
| `application` | Base application composition root, route wiring, and session runner delegation    |
| `launcher`    | Client launcher delivery rendering, shell wrapping, and output dispatching        |
| `parser`      | CLI argument parsing, client registry binding, and PluginConfig resolution        |
| `plugin`      | Dynamic plugin discovery across tiers, contract validation, and client registries |
| `router`      | Command routing, controller dispatching, and route-owned short and detailed help  |
| `routes`      | Reusable official route registrations exported for plugin composition             |

## Design Principles

1. **Contract Compliance** — classes implement abstractions defined in `contract`.
2. **Infrastructure Decoupling** — routing and parsing are completely decoupled from concrete client implementations.
3. **Multi-Tier Discovery & Precedence** — `PluginManager` discovers plugins dynamically at runtime across built-ins, PEP 621 entry points, and drop-in folders.
4. **Validation Barrier** — `PluginManager` validates plugin classes prior to registration, preventing faulty third-party code from compromising runtime stability.
5. **Dynamic Collaborator Introspection** — `Application.run` uses dynamic signature introspection (`inspect.signature`) to bind input source hooks (such as `setup_completer`), forwarding route mappings and the active plugin's `assets_dir` with fail-safe backward compatibility for simpler input sources.

`core.OFFICIAL_ROUTES` is an immutable mapping of the reusable built-in plugin routes. `Application` composes it with the selected plugin's `routes` mapping, where plugin values override official registrations with the same name. It then adds protected `help` and `exit` registrations and validates the complete route set before connecting it. Route names remain open-ended strings; collisions with routes already present in the injected router are rejected. An application instance may be reused for the same plugin, but changing plugins requires a new instance because routers do not remove routes.
