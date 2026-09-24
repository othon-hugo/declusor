# Test Suite

Declusor maintains an automated test suite organized by architectural layer and test scope, supported by a first-class, published public testing SDK (`declusor.testing`).

## Test Principles and Conventions

1. **Typed Test Doubles over Fragile Mocks**: Contract boundaries (`IConsole`, `IConnection`, `IClientFileStore`, `IClientRuntime`, `IClientPlugin`, `IRouter`) are fulfilled by deterministic in-memory test doubles in `declusor.testing`. Unconstrained `MagicMock` setups and monkeypatching are eliminated.
2. **Autonomous Plugin Colocation**: Native plugin tests live directly inside `plugins/<plugin>/tests/`, ensuring that plugins remain autonomous and cleanly extractable into independent repositories.
3. **Contract Conformance Verification**: Every plugin (native or third-party) verifies adherence to framework invariants by subclassing `declusor.testing.PluginConformanceTestSuite`.
4. **Defensive Testing & Invariant Validation**: Invariant violations (empty commands, path traversal, unsupported opcodes, invalid arguments) must explicitly assert raised domain exceptions (`config.InvalidOperation`, `config.ParserError`, `config.RouterError`, `config.ConnectionError`).
5. **Strict Static Type Checking**: Test suites are type-checked with `mypy --strict` alongside production code (`mypy src plugins tests`). All test fixtures, test doubles, and helper functions declare complete, non-`Any` type signatures.
6. **No Cross-Layer Contamination**: Test doubles decouple unit tests from real operating system resources (network sockets, standard I/O, filesystem changes outside `tmp_path`).

## Running the Tests and Quality Checks

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
