---
name: declusor-testing-workflow
description: Procedures, quality standards, and command sequences for running, writing, and verifying tests in the Declusor repository. Use before completing any code changes or adding new tests.
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

Before submitting or committing any change, run the verification chain via the project `Makefile`:

```bash
# Full quality check across entire codebase (format-check, lint, type-check, tests)
make check

# Granular verification targets
make format-check       # Verify Ruff formatting
make format             # Automatically format code and apply safe fixes
make lint               # Run Ruff linter checks
make type-check         # Run Mypy strict type analysis across host and plugins
make test               # Run Pytest suite across host and plugins
make compile            # Verify bytecode compilation across src, tests, and plugins

# Plugin-specific targets
make check-plugin PLUGIN=<plugin_name>  # Full check for a specific plugin
make test-plugin PLUGIN=<plugin_name>   # Run tests for a specific plugin
make test-plugins                       # Run tests across all plugins
```

All checks must pass with 0 errors.
