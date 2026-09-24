# Test Suite Architecture

Declusor maintains an automated test suite organized by architectural layer and test scope, supported by a first-class, published public testing SDK (`declusor.testing`).

## 1. Directory Layout

```text
declusor/
├── src/declusor/testing/     # Shipped, public testing SDK for host & plugin authors
│   ├── doubles/              # Typed doubles for IConsole, IConnection, IClientRuntime, etc.
│   ├── factories.py          # create_test_session, create_dummy_client_config, etc.
│   ├── conformance.py        # Reusable PluginConformanceTestSuite for plugin validation
│   └── pytest_plugin.py      # Standard pytest fixtures (dummy_console, test_session, etc.)
├── plugins/                  # Autonomous native plugin packages
│   ├── shell_socket/         # pyproject.toml, src/shell_socket/, tests/, assets/
│   └── py_socket/            # pyproject.toml, src/py_socket/, tests/, assets/
└── tests/                    # Host-level component, integration, and e2e test suite
    ├── conftest.py           # Loads declusor.testing.pytest_plugin
    ├── unit/
    │   ├── command/          # Command DTO validation and command operation lifecycles
    │   ├── config/           # Settings, BasePath, DataPaths, enums, and centralized exceptions
    │   ├── contract/         # Abstract contracts, SessionContext coordinator, and interfaces
    │   ├── controller/       # Controller handlers and parameter extraction
    │   ├── core/             # Router, DeclusorParser, and PluginManager discovery
    │   ├── main/             # Composition root (Application) and CLI entrypoint (main)
    │   ├── presentation/     # Console I/O, error formatting, and PromptCLI loop
    │   ├── testing/          # Unit verification of testing doubles and factories
    │   └── util/             # Primitives: encoding, security, storage, network, concurrency, parsing
    ├── integration/
    │   └── test_plugin_discovery_e2e.py  # Multi-tier plugin discovery and DI wiring
    └── e2e/                  # End-to-end live session scenarios
```

## 2. Test Principles and Conventions

1. **Typed Test Doubles over Fragile Mocks**: Contract boundaries (`IConsole`, `IConnection`, `IClientFileStore`, `IClientRuntime`, `IClientPlugin`, `IRouter`) are fulfilled by deterministic in-memory test doubles in `declusor.testing`. Unconstrained `MagicMock` setups and monkeypatching are eliminated.
2. **Autonomous Plugin Colocation**: Native plugin tests live directly inside `plugins/<plugin>/tests/`, ensuring that plugins remain autonomous and cleanly extractable into independent repositories.
3. **Contract Conformance Verification**: Every plugin (native or third-party) verifies adherence to framework invariants by subclassing `declusor.testing.PluginConformanceTestSuite`.
4. **Defensive Testing & Invariant Validation**: Invariant violations (empty commands, path traversal, unsupported opcodes, invalid arguments) must explicitly assert raised domain exceptions (`config.InvalidOperation`, `config.ParserError`, `config.RouterError`, `config.ConnectionError`).
5. **Strict Static Type Checking**: Test suites are type-checked with `mypy --strict` alongside production code (`mypy src plugins tests`). All test fixtures, test doubles, and helper functions declare complete, non-`Any` type signatures.
6. **No Cross-Layer Contamination**: Test doubles decouple unit tests from real operating system resources (network sockets, standard I/O, filesystem changes outside `tmp_path`).

## 3. Public Test Doubles & Fixtures (`declusor.testing`)

The `declusor.testing` package is distributed with Declusor, allowing both internal tests and third-party plugin authors to consume it:

| Double                           | Implements                    | Key Capabilities                                                                                                  |
| :------------------------------- | :---------------------------- | :---------------------------------------------------------------------------------------------------------------- |
| `testing.DummyConsole`           | `contract.IConsole`           | Captures messages, binary data, errors, warnings; simulates input queue; tests `KeyboardInterrupt`.               |
| `testing.DummyConnection`        | `contract.IConnection`        | Enforces state transitions (`CREATED` $\to$ `CONNECTED` $\to$ `CLOSED`), records frames, streams incoming chunks. |
| `testing.DummyConnectionProfile` | `contract.IConnectionProfile` | Configurable command rendering per `OperationCode`, default opcode token generation, call history.                |
| `testing.DummyClientFileStore`   | `contract.IClientFileStore`   | In-memory library byte streaming, script templating, modular payload registration.                                |
| `testing.DummyClientRuntime`     | `contract.IClientRuntime`     | Produces dummy connections, exposes bootstrap scripts without touching disk.                                      |
| `testing.DummyClientPlugin`      | `contract.IClientPlugin`      | Self-contained plugin for testing discovery, parser configuration, and runtime instantiations.                    |
| `testing.DummyRouter`            | `contract.IRouter`            | Dynamic controller registration, route inspection, usage documentation, `RouterError` dispatch.                   |
| `testing.DummySocket`            | OS Socket Interface           | In-memory socket buffer simulation (`recv`, `send`, `sendall`, `close`) without OS network ports.                 |
| `testing.DummyApplication`       | `main.Application`            | In-memory CLI execution double tracking parse/run calls and simulating parser and runtime errors.                 |

## 4. Running the Tests and Quality Checks

Run the complete test suite (both host tests and colocated plugin tests):

```bash
pytest
```

Run tests for a specific plugin:

```bash
pytest plugins/shell_socket/tests/ -v
pytest plugins/py_socket/tests/ -v
```

Run tests for a specific host layer:

```bash
pytest tests/unit/command/ -v
pytest tests/unit/controller/ -v
pytest tests/unit/presentation/ -v
pytest tests/integration/ -v
```

Run static type checking across source, plugins, and tests:

```bash
mypy src plugins tests
```

Run linter checks:

```bash
ruff check src plugins tests
```
