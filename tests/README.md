# Test Suite

Declusor maintains an enterprise-grade automated test suite organized by architectural layer and test scope, supported by a first-class, published public testing SDK (`declusor.testing`).

## Architectural Structure

The test suite is structured into partitioned directories corresponding strictly to the application's architectural layers:

```text
tests/
├── e2e/                     # End-to-end integration scenarios (REPL loops, stream redirection, CLI workflows)
└── unit/                    # Isolated component-level unit tests across all 11 architectural layers
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
    └── util/                # Stateless primitives, concurrency task pools, security, and storage helpers
```

Native client transport plugins maintain colocated test suites within their autonomous package trees (`plugins/<plugin>/tests/`).

---

## Test Principles and Conventions

1. **Class-Based Test Suite Grouping**: Every test file groups related test methods into cohesive classes (`class Test<Component><Aspect>:` or `class Test<UnitOfWork>:`). Loose top-level test functions are strictly forbidden. This produces clean hierarchical reporting in pytest (`test_module.py::TestClass::test_method`), isolates test scenarios, and provides clean class-level fixture scoping.
2. **Typed Test Doubles over Fragile Mocks**: Contract boundaries (`IView`, `IInputSource`, `IConnection`, `ITransport`, `ITransportListener`, `IPluginProcessor`, `IPluginRuntime`, `IPluginExtension`, `IRouter`, `IApplication`) are fulfilled by deterministic in-memory test doubles in `declusor.testing`. Unconstrained `MagicMock` setups and fragile monkeypatching are eliminated.
3. **Autonomous Plugin Colocation**: Native plugin tests live directly inside `plugins/<plugin>/tests/`, ensuring that plugins remain autonomous and cleanly extractable into independent repositories.
4. **Contract Conformance Verification**: Every plugin verifies adherence to framework invariants by subclassing `declusor.testing.PluginConformanceTestSuite`.
5. **Defensive Testing & Invariant Validation**: Invariant violations (empty commands, path traversal, unsupported opcodes, invalid arguments) must explicitly assert raised domain exceptions (`config.InvalidOperation`, `config.ParserError`, `config.RouterError`, `config.ConnectionError`, `config.CommandValidationError`).
6. **Strict Static Type Checking**: Test suites are type-checked with `mypy --strict` alongside production code (`mypy src plugins tests`). All test fixtures, test doubles, and helper functions declare complete, non-`Any` type signatures.
7. **No Cross-Layer Contamination**: Test doubles decouple unit tests from real operating system resources (network sockets, standard I/O, filesystem changes outside `tmp_path`).
8. **Dual-Channel Stream Isolation**: Presentation and CLI composition tests strictly isolate raw binary byte streams (`sys.stdout.buffer`) from formatted text streams (`sys.stdout`), ensuring zero stream leakage across test runners.

---

## Testing SDK Catalog (`declusor.testing`)

The public testing SDK provides pre-registered fixtures and typed doubles:

| Test Double | Purpose / Responsibility |
| :--- | :--- |
| `DummyView` | Simulates presentation output; captures `messages`, `errors`, `warnings`, `info`, and `binary_data`. |
| `DummyInputSource` | Simulates operator input queues and command reading; tracks prompt history and simulates EOF. |
| `DummyConnection` | Full state machine (`CREATED` -> `CONNECTED` -> `CLOSED`); records written frames and streams incoming chunks. |
| `DummyConnectionProfile` | Simulates target opcode rendering (`EXEC_COMMAND`, `EXEC_CODE`, `LOAD_MODULE`). |
| `DummyPluginFileStore` | In-memory file, library, and module streaming for plugin asset staging. |
| `DummyPluginRuntime` | Deterministic connection creation injecting configured test doubles. |
| `DummyPlugin` | Self-contained test plugin conforming to `IPluginExtension` for discovery and wiring tests. |
| `DummyRouter` | In-memory route registration, route inspection, usage documentation, and dispatching. |
| `DummySocket` | In-memory byte buffers simulating socket send/recv without OS network binding. |
| `DummyTransport` | In-memory `ITransport` implementation recording transmitted byte frames. |
| `MemoryTransport` & `MemoryTransportListener` | Connected duplex in-memory transport pair and listener for physical transport testing. |
| `DummyApplication` | In-memory CLI execution double tracking `parse` and `run` calls. |
| `PluginConformanceTestSuite` | Reusable conformance test harness asserting plugin metadata, parser configuration, config builder, validation barrier, and runtime creation. |

---

## Running the Tests (Memory-Isolated Sessions)

To prevent process memory saturation and OOM crashes during test execution, tests are partitioned into isolated sessions executed via `make`:

```bash
# Full quality check (formatting, linting, strict typing, and memory-isolated tests)
make check

# Run all test suites across memory-isolated processes sequentially
make test

# Run component unit tests across all 11 core packages
make test-unit

# Run end-to-end interactive REPL and CLI integration scenarios
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
