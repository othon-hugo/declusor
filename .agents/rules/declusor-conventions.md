# Declusor Coding Conventions & Quality Invariants

This document establishes the mandatory conventions, import styles, formatting invariants, and quality standards for all code in this repository.

## Import Conventions

### Namespace Imports

Always import the package namespace directly rather than destructuring separated symbols from deep modules:

```python
# CORRECT: Clean namespace qualification
from declusor import command, config, contract, core, presentation, testing, util

session = contract.SessionContext(...)
console = testing.DummyConsole()
cmd = command.ExecuteCommand(dto)
```

```python
# FORBIDDEN: Destructuring separated symbols across layers
from declusor.testing import DummyConsole, DummyConnection
from declusor.presentation import PromptCLI
from declusor.main.app import Application
```

### Exception Re-exports per Package

Each subpackage re-exports its domain exceptions from `declusor.config` within its `__init__.py` and lists them in `__all__`:

| Package        | Re-exported Exceptions                                                                                          |
| :------------- | :-------------------------------------------------------------------------------------------------------------- |
| `command`      | `CommandError`, `CommandValidationError`, `InvalidOperation`                                                    |
| `contract`     | `ConnectionClosed`, `ConnectionError`, `ConnectionHandshakeError`, `ConnectionTimeoutError`, `InvalidOperation` |
| `controller`   | `ControllerError`                                                                                               |
| `core`         | `ParserError`, `PluginError`, `PluginValidationError`, `RouterError`                                            |
| `presentation` | `PromptError`                                                                                                   |

When handling or raising layer-specific errors, consumers can import them directly from the relevant package namespace (e.g. `core.ParserError`, `command.CommandError`).

## Code Formatting & Documentation Invariants

### Docstring Rhythm (Blank Line Separation)

**Never glue docstrings directly to executable code.** Always insert exactly one blank line between the closing triple quotes (`"""`) of a docstring and the first line of code inside functions, methods, and nested controllers:

```python
# CORRECT
def test_something() -> None:
    """Verify that something works as expected."""

    result = compute()
    assert result is True
```

```python
# FORBIDDEN (glued docstring)
def test_something() -> None:
    """Verify that something works as expected."""
    result = compute()
    assert result is True
```

### Package README Structure

Every package directory must maintain a `README.md` containing at least:

1. `# <Package Name>`: Top-level section with the package name followed by a concise description of the package's role, dependencies, and architectural context.
2. `## Modules`: A markdown table with columns `Module` and `Responsibility` documenting every module in the package without empty rows.
3. `## Design Principles`: A numbered list detailing the design rationale and architectural guarantees of that layer.

## 3. Testing Discipline & Standards

### Mock-Free Deterministic Test Doubles

Do **not** use unconstrained `unittest.mock.MagicMock` or fragile monkeypatching to satisfy core contracts. Use the typed doubles provided by `declusor.testing`:

- `testing.DummyConsole`: Simulates I/O, error logging, and input queues.
- `testing.DummyConnection`: Full state machine (`CREATED` -> `CONNECTED` -> `CLOSED`), frame recording, and chunk streaming.
- `testing.DummyConnectionProfile`: Script rendering and command formatting.
- `testing.DummyClientFileStore`: In-memory file, library, and module streaming.
- `testing.DummyClientRuntime`: Deterministic connection creation.
- `testing.DummyClientPlugin`: Self-contained client plugin for discovery and registration tests.
- `testing.DummyRouter`: Route inspection, usage docs, and deterministic dispatching.
- `testing.DummySocket`: In-memory byte buffers simulating socket send/recv without OS network binding.
- `testing.DummyApplication`: In-memory CLI execution double tracking `parse` and `run` calls.

### Strict Typing Invariant

- Every function, method, fixture, and test must be fully typed.
- `mypy src plugins tests` must pass with zero errors under `--strict`.
- Never use untyped `Any` where a generic `TypeVar` or structural protocol can be specified.
