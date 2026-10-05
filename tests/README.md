# Test Suite

Declusor maintains an automated test suite organized by architectural layer and test scope, supported by the public testing SDK (`declusor.testing`).

## Architectural Structure

The test suite is structured into partitioned directories corresponding strictly to the application's architectural layers:

```text
tests/
├── e2e/                     # End-to-end integration scenarios (REPL loops, stream redirection, CLI workflows)
└── unit/                    # Component and adapter-boundary tests across 11 architectural packages
    ├── app/                 # Application bootstrap, CLI wiring, and terminal application factories
    ├── command/             # Encapsulated command operations, streaming loops, and immutable DTOs
    ├── config/              # Centralized domain exceptions, settings, paths, and operational enums
    ├── contract/            # Domain interfaces, state machines, and session context invariants
    ├── controller/          # Application handlers, request parsing, and ControllerResult signals
    ├── core/                # Infrastructure services, router, parser, and plugin manager
    ├── main/                # Composition roots, CLI argument parsing, and dual-channel stream isolation
    ├── presentation/        # Readline input, formatting views, completers, and prompt loops
    ├── testing/             # Precision tests for the public testing SDK doubles, factories, and fixtures
    ├── transport/           # Physical byte-stream transports, listeners, and composable decorators
    └── util/                # Stateless primitives, concurrency, security, storage, and lang subpackage
```

Native client transport plugins maintain colocated test suites within their autonomous package trees (`plugins/<plugin>/tests/`).

## Test Principles and Conventions

1. **Class-Based Test Suite Grouping**: Every test file groups related test methods into cohesive classes (`class Test<Component><Aspect>:` or `class Test<UnitOfWork>:`). Loose top-level test functions are strictly forbidden. This produces clean hierarchical reporting in pytest (`test_module.py::TestClass::test_method`), isolates test scenarios, and provides clean class-level fixture scoping.
2. **Typed Test Doubles over Fragile Mocks**: Contract boundaries (`IView`, `IInputSource`, `IConnection`, `ITransport`, `ITransportListener`, `IPluginProcessor`, `IPluginRuntime`, `IPluginExtension`, `IRouter`, `IApplication`) are fulfilled by deterministic in-memory test doubles in `declusor.testing`. Unconstrained `MagicMock` setups and fragile monkeypatching are eliminated.
3. **Autonomous Plugin Colocation**: Native plugin tests live directly inside `plugins/<plugin>/tests/`, ensuring that plugins remain autonomous and cleanly extractable into independent repositories.
4. **Contract Conformance Verification**: Every plugin verifies adherence to framework invariants by subclassing `declusor.testing.PluginConformanceTestSuite`.
5. **Defensive Testing & Invariant Validation**: Invariant violations (empty commands, path traversal, unsupported opcodes, invalid arguments) must explicitly assert raised domain exceptions (`config.InvalidOperation`, `config.ParserError`, `config.RouterError`, `config.ConnectionError`, `config.CommandValidationError`).
6. **Configured Static Type Checking**: Test suites are checked with the repository's strict mypy profile (`make type-check`). The profile contains explicit `Any`-related exceptions in `pyproject.toml`; public APIs and test helpers should still use precise types.
7. **Controlled Resource Boundaries**: Most component tests use typed doubles and `tmp_path`. Tests for the TCP listener and socket adapter use loopback or ephemeral sockets only; they must not depend on external hosts and must close resources deterministically.
8. **Dual-Channel Stream Isolation**: Presentation and CLI composition tests strictly isolate raw binary byte streams (`sys.stdout.buffer`) from formatted text streams (`sys.stdout`), ensuring zero stream leakage across test runners.

## Coverage Ownership

| Behavior under test                                                                      | Owning test level   | Primary location / command                                                         |
| :--------------------------------------------------------------------------------------- | :------------------ | :--------------------------------------------------------------------------------- |
| Public package exports and import surfaces                                               | Unit                | `tests/unit/<package>/test_init.py`; `make test-unit`                              |
| DTO validation, function branches, state transitions, and error translation              | Unit                | `tests/unit/<package>/`; `make test-unit`                                          |
| Socket adapter behavior at the OS boundary                                               | Unit boundary tests | `tests/unit/transport/`; loopback only, run via `make test-unit`                   |
| Application startup, REPL routing, real client handshake, command response, and teardown | E2E                 | `tests/e2e/`; `make test-e2e`                                                      |
| Plugin-specific framing, assets, renderer, and native client behavior                    | Plugin              | `plugins/<plugin>/tests/`; `make test-plugins` or `make test-plugin PLUGIN=<name>` |
| Shared plugin extension requirements                                                     | Conformance         | Plugin `test_conformance.py` subclasses `PluginConformanceTestSuite`               |

Each test should have one primary behavior and one clear owner. Unit tests cover branches and local contracts; end-to-end tests cover cross-layer workflows without duplicating every unit edge case; plugin suites cover implementation-specific protocol behavior. Prefer the shared conformance suite for common plugin requirements and keep plugin tests for behavior unique to that implementation. Every source package `__all__` has an export check; root `declusor` and `declusor.testing.doubles` checks live in `tests/unit/testing/test_init.py`, and the `util.lang` check is nested under `tests/unit/util/lang/`.

## Testing SDK Catalog (`declusor.testing`)

The public testing SDK provides pre-registered fixtures and typed doubles:

| Test Double                                   | Purpose / Responsibility                                                                                                                     |
| :-------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------- |
| `DummyView`                                   | Simulates presentation output; captures `messages`, `errors`, `warnings`, `info`, and `binary_data`.                                         |
| `DummyInputSource`                            | Simulates operator input queues and command reading; tracks prompt history and simulates EOF.                                                |
| `DummyConnection`                             | Full state machine (`CREATED` -> `CONNECTED` -> `CLOSED`); records written frames and streams incoming chunks.                               |
| `DummyOperationRenderer`                      | Simulates target opcode rendering (`EXEC_COMMAND`, `EXEC_CODE`, `LOAD_MODULE`).                                                              |
| `DummyPluginFileStore`                        | In-memory file, library, and module streaming for plugin asset staging.                                                                      |
| `DummyPluginRuntime`                          | Deterministic connection creation injecting configured test doubles.                                                                         |
| `DummyPlugin`                                 | Self-contained test plugin conforming to `IPluginExtension` for discovery and wiring tests.                                                  |
| `DummyRouter`                                 | In-memory route registration, route inspection, usage documentation, and dispatching.                                                        |
| `DummySocket`                                 | In-memory byte buffers simulating socket send/recv without OS network binding.                                                               |
| `DummyTransport`                              | In-memory `ITransport` implementation recording transmitted byte frames.                                                                     |
| `MemoryTransport` & `MemoryTransportListener` | Connected duplex in-memory transport pair and listener for physical transport testing.                                                       |
| `DummyApplication`                            | In-memory CLI execution double tracking `parse` and `run` calls.                                                                             |
| `PluginConformanceTestSuite`                  | Reusable conformance test harness asserting plugin metadata, parser configuration, config builder, validation barrier, and runtime creation. |

## Running the Tests (Memory-Isolated Sessions)

To prevent process memory saturation and OOM crashes during test execution, tests are partitioned into isolated sessions executed via `make`:

```bash
# Full quality check (formatting, linting, configured typing, and isolated tests)
make check

# Run all test suites across memory-isolated processes sequentially
make test

# Run component and adapter-boundary tests across all 11 core packages
make test-unit

# Run full application, REPL, CLI, and real-client workflows
make test-e2e

# Run autonomous plugin tests across all colocated plugin packages
make test-plugins

# Run tests for a specific package during iterative development
.venv/bin/pytest tests/unit/command -v
.venv/bin/pytest tests/unit/presentation -v

# Run tests for a specific plugin package
make test-plugin PLUGIN=shell_socket
make test-plugin PLUGIN=py_socket
```
