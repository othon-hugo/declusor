# Test Suite Architecture

Declusor maintains an automated test suite organized by architectural layer and test scope, supported by a dedicated package of typed test doubles.

## 1. Directory Layout

```text
tests/
├── testing/             # Reusable, fully-typed test doubles and factory builders
│   ├── doubles.py       # Dummies for IConsole, IConnection, IClientRuntime, IRouter, etc.
│   └── factories.py     # create_test_session, create_dummy_client_config, etc.
├── conftest.py          # Root pytest fixtures exposing typed test doubles
├── unit/
│   ├── command/         # Command DTO validation and command operation lifecycles
│   ├── config/          # Settings, BasePath, DataPaths, enums, and centralized exceptions
│   ├── contract/        # Abstract contracts, SessionContext coordinator, and interfaces
│   ├── controller/      # Controller handlers and parameter extraction
│   ├── core/            # Router, DeclusorParser, and PluginManager discovery
│   ├── main/            # Composition root (Application) and CLI entrypoint (main)
│   ├── plugins/         # Autonomous client plugins (shell_socket, py_socket)
│   ├── presentation/    # Console I/O, error formatting, and PromptCLI loop
│   ├── testing/         # Unit verification of testing doubles and factories
│   └── util/            # Primitives: encoding, security, storage, network, concurrency, parsing
├── integration/
│   └── test_plugin_discovery_e2e.py  # End-to-end multi-tier plugin discovery
└── e2e/                 # End-to-end live session scenarios
```

## 2. Test Principles and Conventions

1. **Typed Test Doubles over Fragile Mocks**: Contract boundaries (`IConsole`, `IConnection`, `IClientFileStore`, `IClientRuntime`, `IClientPlugin`, `IRouter`) are fulfilled by deterministic in-memory test doubles in `tests/testing/`. Repetitive `MagicMock` setups and monkeypatching are replaced with typed fixtures from `tests/conftest.py`.
2. **Defensive Testing & Invariant Validation**: Invariant violations (empty commands, path traversal, unsupported opcodes, invalid arguments) must explicitly assert raised domain exceptions (`config.InvalidOperation`, `config.ParserError`, `config.RouterError`, `config.ConnectionError`).
3. **Strict Static Type Checking**: Test suites are type-checked with `mypy --strict` alongside production code (`mypy src tests`). All test fixtures, test doubles, and helper functions declare complete, non-`Any` type signatures.
4. **No Cross-Layer Contamination**: Test doubles decouple unit tests from real operating system resources (network sockets, standard I/O, filesystem changes outside `tmp_path`).

## 3. Test Doubles & Fixtures (`tests/testing/`)

The `tests.testing` package provides contracts implementations ready for pytest dependency injection:

| Double                   | Implements                    | Key Capabilities                                                                                                     |
| :----------------------- | :---------------------------- | :------------------------------------------------------------------------------------------------------------------- |
| `DummyConsole`           | `contract.IConsole`           | Captures messages, binary data, errors, warnings; simulates input queue; tests `KeyboardInterrupt`.                  |
| `DummyConnection`        | `contract.IConnection`        | Simulates state transitions (`CREATED` -> `CONNECTED` -> `CLOSED`), records written frames, streams incoming chunks. |
| `DummyConnectionProfile` | `contract.IConnectionProfile` | Configurable command rendering per `OperationCode`, default opcode token generation, call history.                   |
| `DummyClientFileStore`   | `contract.IClientFileStore`   | In-memory library byte streaming, script templating, modular payload registration.                                   |
| `DummyClientRuntime`     | `contract.IClientRuntime`     | Produces dummy connections, exposes bootstrap scripts without touching disk.                                         |
| `DummyClientPlugin`      | `contract.IClientPlugin`      | Self-contained plugin for testing discovery, parser configuration, and runtime instantiations.                       |
| `DummyRouter`            | `contract.IRouter`            | Dynamic controller registration, route inspection, usage documentation, `RouterError` dispatch.                      |
| `DummySocket`            | OS Socket Interface           | In-memory socket buffer simulation (`recv`, `send`, `sendall`, `close`) without OS network ports.                    |
| `DummyApplication`       | `main.Application`            | In-memory CLI execution double tracking parse/run calls and simulating parser and runtime errors.                    |

## 4. Running the Tests and Quality Checks

Run the complete test suite:

```bash
pytest tests -v
```

Run tests for a specific layer:

```bash
pytest tests/unit/command/ -v
pytest tests/unit/controller/ -v
pytest tests/unit/presentation/ -v
pytest tests/unit/plugins/ -v
```

Run static type checking across source and tests:

```bash
mypy src tests
```

Run linter checks:

```bash
ruff check tests src plugins
```
