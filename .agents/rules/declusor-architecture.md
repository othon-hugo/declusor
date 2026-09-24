# Declusor Architecture & Layering Rules

This document specifies the architectural boundaries, layering rules, and package invariants for the Declusor repository.

## Architectural Layers & Dependency Direction

Dependencies must flow strictly downwards from composition roots to foundational primitives:

```text
main (Composition Root)
  ├── core (Infrastructure, Registries, Routing, Parser)
  ├── controller (Application Layer & Handlers)
  ├── command (Encapsulated Operations & DTOs)
  ├── presentation (Terminal REPL & Console View)
  └── contract (Domain Interfaces & State Machines)
        ├── util (Stateless Primitives & Helpers)
        └── config (Constants, Enums, Settings, Exceptions)
```

### Layer Constraints & Invariants

1. **`config` (Foundation Base)**:
   - **Zero dependencies** on any other package in `declusor`.
   - Defines centralized domain exceptions (`DeclusorException`), operational enums (`OperationCode`, `ConnectionState`, `ControllerAction`), and path settings (`DataPaths`).
2. **`util` (Stateless Primitives)**:
   - Depends **only** on `config`.
   - Zero circular dependencies. All functions are pure, stateless, or defensive.
   - When functions handle abstractions from higher layers (e.g. `import_plugin_from_file`), they **must use generic `TypeVar`** rather than importing contracts directly.
3. **`contract` (Domain Layer)**:
   - Depends **only** on `config` and `util`.
   - Pure interfaces (`@abstractmethod`), state machines (`IConnection`), and data coordinators (`SessionContext`).
   - Must have **zero dependencies** on implementation packages (`core`, `command`, `controller`, `presentation`, `main`, or `plugins`).
4. **`command` (Command Pattern)**:
   - Encapsulates single operations (`ExecuteCommand`, `ExecuteFile`, `UploadFile`, `LoadModule`, `LaunchShell`).
   - Uses immutable DTOs (`ExecuteCommandDTO`, etc.) with fail-fast invariant validation.
5. **`controller` (Application Handlers)**:
   - Thin handlers parsing requests, creating command DTOs, and dispatching via `SessionContext.execute()`.
   - Returns structured `ControllerResult(action=ControllerAction.CONTINUE | TERMINATE)` lifecycle signals instead of relying on control-flow exceptions.
6. **`core` (Infrastructure Services)**:
   - Implements `IRouter` (`Router`), `IParser` (`DeclusorParser`), and `PluginManager`.
   - Completely decoupled from concrete plugin implementations.
7. **`presentation` (View Layer)**:
   - Manages readline terminal I/O (`Console`) and the interactive prompt execution loop (`PromptCLI`).
   - Interacts with controllers exclusively via route dispatching and `ControllerResult` signals.
8. **`main` (Composition Root)**:
   - Bootstraps registries, discovers plugins, wires core routes, and runs the application.
   - Entrypoint function `main(argv)` catches all exceptions, prints user-friendly messages, and maps to deterministic exit codes (`0`, `1`, `2`).
9. **`testing` (Public Testing SDK)**:
   - Ships deterministic, fully-typed test doubles (`DummyConsole`, `DummyConnection`, `DummyPluginFileStore`, `DummyPluginRuntime`, etc.) and reusable conformance suites (`PluginConformanceTestSuite`).

## Autonomous Plugin Topology

All native plugins reside under `plugins/<plugin_name>/` as autonomous, self-contained packages:

```text
plugins/<plugin_name>/
├── pyproject.toml         # Standalone package metadata & entry point
├── README.md              # Plugin documentation
├── src/
│   └── <plugin_name>/
│       ├── __init__.py    # Public exports
│       ├── plugin.py      # IPlugin & IPluginRuntime & IClientFileStore implementation
│       └── connection.py  # IConnection, IConnectionProfile
├── assets/                # Self-contained stagers, libraries, and helpers
│   ├── launchers/         # Embedded client bootstrap scripts
│   ├── helpers/           # In-memory helper functions sent during handshake
│   └── modules/           # On-demand modular payloads
└── tests/                 # Dedicated unit and conformance test suite
    ├── conftest.py
    └── test_conformance.py
```

### Plugin Invariants

1. **Isolation Invariant**: Production code in `src/declusor/` and host unit tests in `tests/` **MUST NEVER** import concrete plugins directly (e.g. `import shell_socket`). Tests use test doubles (`DummyPlugin`).
2. **Registration Standard**: Plugins register via the standard entry point group:
   ```toml
   [project.entry-points."declusor.plugins"]
   <plugin_name> = "<plugin_name>:PluginClass"
   ```
3. **Contract Conformance**: Every plugin must pass `PluginConformanceTestSuite` verifying its metadata, parser configuration, config builder, validation barrier, and runtime creation.
