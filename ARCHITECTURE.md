# Declusor Architecture

Declusor is an interactive post-exploitation and command-and-control (C2) framework designed with clean architecture principles.

It emphasizes modularity, separation of concerns, and strict dependency inversion. Dependencies flow strictly downward and inward toward domain abstractions, ensuring testability, runtime safety, and seamless extensibility across an autonomous plugin ecosystem.

## Architectural Principles

### Dependency Inversion & Contract-First Design

- Higher-level layers and core infrastructure depend strictly on abstract domain contracts, never on concrete implementations.
- The domain layer defines formal interfaces, transport state machines, and session coordinators without framework or transport-specific logic.
- Transport mechanisms and agent runtimes implement these abstractions externally, preventing any coupling between the host engine and concrete protocols.

### Autonomous Plugin Self-Contention

- Plugins are fully autonomous packages maintained in independent source trees with individual packaging manifests, assets, and test suites.
- Each plugin encapsulates its own transport implementation, protocol profile, and bundled client assets (stagers, helpers, and payloads).
- Core framework code and host unit tests never import concrete plugin packages directly. All coupling is mediated through domain contracts and discovery mechanisms.

### Multi-Tier Dynamic Discovery & Validation Barriers

- The system discovers plugins dynamically at runtime across multiple source tiers:
  1. **Built-in Plugins**: Shipped repository packages located in the plugins workspace.
  2. **Python Entry Points**: Standard distribution packages registered via entry points (`declusor.plugins`).
  3. **Operator Directories**: Custom drop-in directories specified via configuration or CLI parameters.
- A strict validation barrier verifies candidate plugins against domain contracts prior to registration, preventing faulty third-party code from compromising runtime stability.

### Declarative Signal-Driven Flow Control

- Application controllers return explicit lifecycle signals (`CONTINUE`, `TERMINATE`) wrapped in structured result objects.
- Normal control flow is never driven by exceptions; domain exceptions represent exceptional errors and propagate to central handlers for deterministic reporting and process exit codes.

### Dynamic Signature Introspection

- Application and transport factories dynamically inspect parameter signatures via `inspect.signature` rather than relying on fragile exception-catching.
- This allows flexible dependency injection (e.g. `listener_factory`, `launcher_renderer`) while propagating genuine internal errors transparently.

### Dual-Channel Stream Isolation

- Console I/O strictly isolates raw binary streaming (`sys.stdout.buffer`) from formatted human-readable text output (`sys.stdout`).
- Presentation formatters and CLI drivers prevent binary corruption and ensure deterministic dual-stream assertion in automated test environments.

### First-Class Testing SDK & Mock-Free Verification

- Reusable test infrastructure is shipped as a first-class package within the project (`declusor.testing`).
- Tests rely on deterministic, fully-typed test doubles (`DummyView`, `DummyConnection`, `DummyTransport`, `MemoryTransport`, `DummyRouter`, etc.) and automated contract conformance suites (`PluginConformanceTestSuite`) rather than fragile, untyped mock monkeypatching.
- The test suite is organized into 100% class-grouped suites (`class Test<Component><Aspect>:`) and executed across memory-isolated Python sessions.

## Layer Architecture & Dependency Model

Dependencies flow strictly downward from composition roots to foundational primitives:

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

- **Composition Root & Application Bootstrap**
  - **`main`**: CLI entrypoint, argument parsing, error trapping, exit code mapping, and dynamic application execution.
    - _Depends on_: `app`, `core`, `presentation`, `contract`, `util`, `config`
  - **`app`**: Application flavors and bootstrap factories (e.g. `create_terminal_application`).
    - _Depends on_: `core`, `transport`, `presentation`, `controller`, `contract`, `config`
- **Presentation**
  - **`presentation`**: Terminal REPL interactive prompt loop, readline input source, autocomplete completer, and console view.
    - _Depends on_: `contract`, `util`, `config`
- **Application**
  - **`controller`**: Application flow handlers, request parsing, command DTO instantiation, and structured `ControllerResult` signal emission.
    - _Depends on_: `command`, `contract`, `util`, `config`
  - **`command`**: Encapsulated discrete operations via immutable, self-validating DTOs (`ExecuteCommand`, `UploadFile`, etc.).
    - _Depends on_: `contract`, `util`, `config`
- **Infrastructure & Transport**
  - **`core`**: Infrastructure services (`DeclusorParser`, `Router`, `PluginManager`, `LauncherRenderer`, `Application`).
    - _Depends on_: `contract`, `transport`, `util`, `config`
  - **`transport`**: Physical network byte-stream channels (`SocketTransport`, `TcpListener`) and composable decorators (`XorTransport`, `TransportPipeline`).
    - _Depends on_: `contract`, `util`, `config`
- **Domain**
  - **`contract`**: Pure domain interfaces (`@abstractmethod`), protocol state machines (`IConnection`), stream contracts (`ITransport`, `ITransportListener`), and session coordinator (`SessionContext`).
    - _Depends on_: `config` (zero dependencies on `util` or implementation layers)
- **Foundations**
  - **`util`**: Pure, stateless helpers (encoding, network, concurrency, security, storage) using generic `TypeVar` signatures.
    - _Depends on_: `config`
  - **`config`**: Foundation base centralizing domain exceptions (`DeclusorException`), operational enums (`OperationCode`, `ConnectionState`), settings, and paths.
    - _Depends on_: Standard library strictly (zero internal dependencies)
- **Ecosystem & Verification**
  - **`plugins`**: Autonomous, self-contained transport packages implementing `contract` interfaces.
    - _Depends on_: `contract`, `config`, `util`
  - **`testing`**: Public test harness supplying typed doubles and reusable conformance suites.
    - _Depends on_: `contract`, `config`

### Dependency Rules & Directional Invariants

| Source Layer (From)               | Target Layer (To)                                            | Permitted? | Rule                                                                          |
| :-------------------------------- | :----------------------------------------------------------- | :--------: | :---------------------------------------------------------------------------- |
| `main`, `app`                     | `core`, `transport`, `controller`, `presentation`            |  **Yes**   | Composition roots wire concrete components and start execution.               |
| `controller`                      | `command`, `contract`, `util`, `config`                      |  **Yes**   | Controllers translate requests into commands and dispatch via domain session. |
| `command`, `core`, `presentation` | `contract`, `util`, `config`                                 |  **Yes**   | Components implement or consume domain interfaces.                            |
| `transport`                       | `contract`, `util`, `config`                                 |  **Yes**   | Transports implement domain stream contracts and use base utilities/config.   |
| `contract`                        | `config`                                                     |  **Yes**   | Domain interfaces rely strictly on base exceptions, settings, and enums.      |
| `util`                            | `config`                                                     |  **Yes**   | Pure utilities depend only on base exceptions and constants.                  |
| `contract`                        | `util`                                                       |   **No**   | Domain abstractions must never depend on stateless utility helpers.           |
| `contract`                        | `core`, `transport`, `command`, `controller`, `presentation` |   **No**   | Domain abstractions must never depend on implementation layers.               |
| `transport`                       | `core`, `command`, `controller`, `presentation`, `main`      |   **No**   | Transport implementations must never depend on higher application layers.     |
| `src/declusor/`                   | concrete plugins                                             |   **No**   | Host code must never import specific plugin packages directly.                |
| Production code                   | `testing`                                                    |   **No**   | Production packages must never depend on test infrastructure.                 |

## High-Level Layer Responsibilities

### Foundations (`config`, `util`)

- **Configuration Base (`config`)**: Sits at the root of the dependency tree with zero internal dependencies. Centralizes domain exceptions, operational enums, and base filesystem paths.
- **Stateless Primitives (`util`)**: Provides pure, defensive helpers for encoding, hashing, path sandboxing, cooperative thread pooling, socket listeners, and file storage validation. Uses structural generics to avoid importing domain contracts.

### Domain (`contract`)

- **Domain Abstractions**: Defines rigid interfaces for clients, runtimes, connections, commands, controllers, routers, consoles, and parsers.
- **State Machine Invariants**: Enforces strict lifecycle transitions (`CREATED` $\to$ `CONNECTED` $\to$ `CLOSED`) and framed streaming rules for remote transport sessions.
- **Session Coordinator**: Encapsulates active session dependencies (transport connection, operator console, asset file store) and coordinates command execution.

### Application (`command`, `controller`)

- **Command Operations (`command`)**: Encapsulates discrete remote tasks (command execution, script execution, file transfer, modular payload loading, interactive shell spawning) using immutable parameter objects with fail-fast validation.
- **Application Controllers (`controller`)**: Serves as the application orchestration layer. Parses user arguments, constructs commands, coordinates execution through the active session, and signals declarative lifecycle actions back to the view loop.

### Infrastructure & Transport (`core`, `transport`)

- **Infrastructure Services (`core`)**: Manages route registration, command usage documentation, command-line argument mapping, and the multi-tier dynamic plugin discovery engine.
- **Physical & Decorator Transports (`transport`)**: Encapsulates raw socket I/O (`SocketTransport`), server listening (`TcpListener`), and composable stream ciphers (`XorTransport`). Implements clean exception translation and protects against stream segmentation desynchronization.

### Presentation (`presentation`)

- **User Interface & Delivery**: Handles operator interaction, readline history, autocomplete, stream formatting, and the interactive REPL execution loop. Operates exclusively through domain contracts and controller action signals.

### Composition Root (`main`, `app`)

- **Application Bootstrap (`main`, `app`)**: Initializes the client registry, discovers plugins across all configured tiers, wires application routes, and executes the active session via specialized application targets (`terminal`).
- **Top-Level Error Barrier**: Handles process arguments, captures domain exceptions, prints user-friendly diagnostic messages, and translates results into deterministic operating system exit codes.

### Ecosystem & Verification (`plugins`, `testing`)

- **Autonomous Transport Plugins (`plugins`)**: Self-contained packages implementing domain contracts, providing dedicated launchers, helpers, on-demand modules, and colocated test suites.
- **Public Testing SDK (`testing`)**: Supplies mock-free, deterministic doubles (`MemoryTransport`, `DummyTransport`, `DummyView`, `DummyConnection`, etc.) for all domain abstractions and provides reusable test suites (`PluginConformanceTestSuite`) that verify plugins against host contract requirements.

## Extensible Plugin Ecosystem

Declusor treats client transports as autonomous, independently versionable packages.

### Autonomous Plugin Package Structure

Plugins follow a standard source layout:

- **Package Manifest (`pyproject.toml`)**: Standalone configuration declaring package metadata, dependencies, and entry-point registration.
- **Source Tree (`src/declusor_<plugin_name>`)**: Implements the plugin contract, runtime adapter, transport state machine, protocol profile, and asset file store.
- **Bundled Assets (`assets/{launchers,helpers,modules}`)**: Embedded launchers (stagers), initialization libraries (helpers), and on-demand payloads (modules).
- **Test Suite (`tests/`)**: Dedicated unit and conformance tests isolated within the plugin directory.

### Asset Overlay Architecture

Plugins bundle default assets within their own directories. Operators can overlay custom stagers, helpers, or modular payloads at runtime without modifying plugin source code:

1. **Launchers (`assets/launchers`)**: One-line stager scripts rendered dynamically with connection host, port, and security tokens.
2. **Helpers (`assets/helpers`)**: Library scripts concatenated and evaluated in-memory during session initialization.
3. **Modules (`assets/modules`)**: On-demand operational scripts loaded dynamically during post-exploitation.

## System Execution Flows

```mermaid
sequenceDiagram
    autonumber
    actor Operator
    participant Main as Composition Root (main/app)
    participant Core as Discovery & Parser (core)
    participant Listener as Listener (transport.TcpListener)
    participant Plugin as Client Plugin (plugins/)
    participant View as Presentation REPL (presentation)
    participant Controller as Controller & Command
    participant Remote as Remote Client Agent

    Operator->>Main: Launch CLI arguments
    Main->>Core: Parse options & discover plugins
    Core->>Plugin: Validate contract & load plugin
    Core-->>Main: Configured client runtime
    Main->>Listener: with listener: accept incoming transport
    Remote->>Listener: Connect TCP socket
    Listener-->>Main: Return ITransport (SocketTransport)
    Main->>Plugin: runtime.create_connection(transport)
    Plugin->>Remote: Initialize session & negotiate helpers (via transport)
    Remote-->>Plugin: Acknowledge handshake (ACK sentinel)
    Main->>View: Start interactive REPL with SessionContext

    loop Interactive Session
        Operator->>View: Enter command line
        View->>Core: Lookup route in table
        Core-->>View: Controller handler
        View->>Controller: Dispatch request with SessionContext
        Controller->>Remote: Send framed command payload
        Remote-->>Controller: Stream chunked output
        Controller->>View: Output chunks to operator console
        Controller-->>View: Return ControllerResult(CONTINUE | TERMINATE)
    end

    View-->>Main: Exit requested or connection closed
    Main->>Plugin: Close transport connection
    Main-->>Operator: Exit process with status code
```

## Architecture Quality & Safety Invariants

1. **Strict Type Safety**: The entire codebase (core framework, native plugins, and test suites) is verified under strict static type checking with zero untyped public APIs (`mypy --strict src plugins tests`).
2. **Mock-Free Testing**: Internal and external tests use typed test doubles and conformance suites, preventing test fragility caused by mock drift.
3. **Class-Based Test Suite Grouping**: All unit, integration, and e2e test files group test cases into intention-revealing test classes (`class Test<Component><Aspect>:`). Loose top-level test functions are strictly forbidden.
4. **Memory-Isolated Test Execution**: Automated testing executes across partitioned, memory-isolated processes (`make test-unit`, `make test-e2e`, `make test-plugins`), eliminating memory accumulation and container OOM risks.
5. **Dual-Channel Stream Isolation**: Complete physical separation of raw binary payloads (`sys.stdout.buffer`) from formatted console output (`sys.stdout`).
6. **Fail-Fast Validation**: Inputs, file paths, and plugin descriptors are validated at system boundaries before entering core execution paths.
7. **Sandboxed File Operations**: All filesystem interactions enforce path-traversal safeguards and extension constraints.
