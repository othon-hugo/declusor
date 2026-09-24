---
name: declusor-testing-workflow
description: >-
  Procedures, quality standards, and command sequences for running, writing, and verifying tests in the Declusor repository. Use before completing any code changes or adding new tests.
---

# Declusor Testing & Verification Workflow

This skill outlines the standard testing procedures, test double usage, and verification commands required for all contributions to Declusor.

## 1. Test Suite Architecture

Declusor test suites are strictly partitioned:

- `tests/unit/`: Component-level tests organized by package (`command/`, `config/`, `contract/`, `controller/`, `core/`, `main/`, `presentation/`, `testing/`, `util/`).
- `tests/integration/`: Cross-layer wiring and multi-tier plugin discovery tests.
- `plugins/<plugin>/tests/`: Autonomous unit and conformance tests for each individual plugin.

## 2. Using `declusor.testing` Doubles

Never mock framework contracts using raw `MagicMock`. Use typed doubles provided by `declusor.testing`:

```python
from declusor import contract, testing

def test_handler(dummy_connection: testing.DummyConnection, dummy_console: testing.DummyConsole) -> None:
    """Always document test intent with a clean pydoc and blank line below."""

    dummy_console.feed_inputs("help", "exit")
    dummy_connection.write(b"data")
    assert dummy_connection.written == [b"data"]
```

Standard typed pytest fixtures are pre-registered via `pytest_plugins = ["declusor.testing.pytest_plugin"]`:

- `dummy_console`: In-memory `IConsole` double
- `dummy_connection`: State-machine `IConnection` double
- `dummy_file_store`: In-memory `IClientFileStore` double
- `dummy_router`: In-memory `IRouter` double
- `dummy_profile`: In-memory `IConnectionProfile` double
- `test_session`: Pre-configured `SessionContext` double
- `dummy_app`: In-memory `Application` double

## 3. Verification Execution Commands

Before submitting or committing any change, run the full verification chain:

```bash
# 1. Full test suite (including colocated plugin tests)
.venv/bin/pytest -q

# 2. Strict static type analysis across host, plugins, and tests
.venv/bin/mypy src plugins tests

# 3. Linting rules
.venv/bin/ruff check src plugins tests

# 4. Code formatting check
.venv/bin/ruff format --check src plugins tests
```

All 4 commands must pass with 0 errors and 0 warnings.
