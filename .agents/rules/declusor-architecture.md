---
trigger: always_on
---

# Declusor Architecture & Layering Rules

This document specifies the architectural boundaries, layering rules, and package invariants for the Declusor repository.

## Architectural Layers & Dependency Direction

Dependencies must flow strictly downwards from composition roots to foundational primitives:

```text
main (Composition Root)
  ├── app (Application Flavors & Bootstrap)
  ├── core (Infrastructure, Registries, Routing, Parser)
  ├── transport (Physical Transports, Listeners, Decorators)
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
   - Defines centralized domain exceptions (`DeclusorException`), operational enums (`OperationCode`, `ConnectionState`, `ControllerAction`), and path constants (`ROOT_DIR`, `PLUGINS_DIR`, `USER_DIR`, `USER_PLUGINS_DIR`).
2. **`util` (Stateless Primitives)**:
   - Depends **only** on `config`.
   - Zero circular dependencies. All functions are pure, stateless, or defensive.
   - When functions handle abstractions from higher layers (e.g. `import_plugin_from_file`), they **must use generic `TypeVar`** rather than importing contracts directly.
3. **`contract` (Domain Layer)**:
   - Depends **only** on `config` and `util`.
   - Pure interfaces (`@abstractmethod`), state machines (`IConnection`), and data coordinators (`SessionContext`).
   - Must have **zero dependencies** on implementation packages (`core`, `command`, `controller`, `presentation`, `main`, or `plugins`).
4. **`command` (Command Pattern)**:
   - Pure interfaces (`@abstractmethod`), state machines (`IConnection`), stream contracts (`ITransport`, `ITransportListener`), and data coordinators (`SessionContext`).
   - Must have **zero dependencies** on implementation packages (`core`, `transport`, `command`, `controller`, `presentation`, `app`, `main`, or `plugins`).
5. **`transport` (Transport Implementations & Decorators)**:
   - Depends **only** on `contract`, `util`, and `config`.
   - Encapsulates physical byte-stream I/O (`SocketTransport`, `TcpListener`) and composable decorators (`XorTransport`).
   - Completely isolates OS network mechanics from session-layer protocols.
   - Zero dependencies on `core`, `command`, `controller`, `presentation`, `app`, `main`, or `plugins`.
6. **`command` (Command Pattern)**:
   - Encapsulates single operations (`ExecuteCommand`, `ExecuteFile`, `UploadFile`, `LoadModule`, `LaunchShell`).
   - Uses immutable DTOs (`ExecuteCommandDTO`, etc.) with fail-fast invariant validation.
7. **`controller` (Application Handlers)**:
8. **`controller` (Application Handlers)**:
   - Thin handlers parsing requests, creating command DTOs, and dispatching via `SessionContext.execute()`.
   - Returns structured `ControllerResult(action=ControllerAction.CONTINUE | TERMINATE)` lifecycle signals instead of relying on control-flow exceptions.
9. **`core` (Infrastructure Services)**:
10. **`core` (Infrastructure Services)**:
    - Implements `IRouter` (`Router`), `IParser` (`DeclusorParser`), and `PluginManager`.
    - Completely decoupled from concrete plugin implementations.
11. **`presentation` (View Layer)**:
12. **`presentation` (View Layer)**:
    - Manages readline terminal input (`TerminalInputSource`), terminal output (`TerminalView`), and the interactive prompt execution loop (`PromptLoop`).
    - Interacts with controllers exclusively via route dispatching and `ControllerResult` signals.
13. **`main` (Composition Root)**:
    - Bootstraps registries, discovers plugins, wires core routes, and runs the application.
    - Entrypoint function `main(argv)` catches all exceptions, prints user-friendly messages, and maps to deterministic exit codes (`0`, `1`, `2`).
14. **`testing` (Public Testing SDK)**:
    - Ships deterministic, fully-typed test doubles (`DummyView`, `DummyInputSource`, `DummyConnection`, `DummyPluginFileStore`, `DummyPluginRuntime`, etc.) and reusable conformance suites (`PluginConformanceTestSuite`).
15. **`app` (Application Flavors & Bootstrap)**:
    - Assembles application targets (e.g. `terminal`) by composing `core`, `transport`, `presentation`, and `controller`.
    - Exposes clean bootstrap factories (`create_terminal_application`).
16. **`main` (Composition Root)**:
    - Bootstraps registries, discovers plugins, wires core routes, and runs the application.
    - Entrypoint function `main(argv)` catches all exceptions, prints user-friendly messages, and maps to deterministic exit codes (`0`, `1`, `2`).
17. **`testing` (Public Testing SDK)**:
    - Ships deterministic, fully-typed test doubles (`DummyView`, `DummyInputSource`, `DummyConnection`, `DummyTransport`, `MemoryTransport`, `MemoryTransportListener`, `DummyPluginFileStore`, `DummyPluginRuntime`, etc.) and reusable conformance suites (`PluginConformanceTestSuite`).

## Autonomous Plugin Topology

All native plugins reside under `plugins/<plugin_name>/` as autonomous, self-contained packages:

```text
plugins/<plugin_name>/
├── pyproject.toml         # Standalone package metadata & entry point
├── README.md              # Plugin documentation
├── src/
│   └── <plugin_name>/
│       ├── __init__.py    # Public exports
│       ├── plugin.py      # IPluginExtension, IPluginRuntime, and IPluginProcessor implementation
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
