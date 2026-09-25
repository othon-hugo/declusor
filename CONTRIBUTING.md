# Contributing to Declusor

Thank you for your interest in contributing to **Declusor**! This document provides the architectural principles, quality standards, coding invariants, and workflows required to contribute effectively to this repository.

## Architectural Overview & Boundaries

Declusor is architected around clean, decoupled layers with strict unidirectional dependency flow:

### Foundations

1. **`config` (Foundation Base)**:
   - Depends strictly on the standard library.
   - Centralizes domain exceptions, configuration constants, settings, and enums.
2. **`util` (Stateless Primitives)**:
   - Depends only on `config` and standard library primitives.
   - Pure, stateless helpers (encoding, network, concurrency) with zero domain knowledge.
   - Used by infrastructure, presentation, commands, and plugins; never imported or depended upon by `contract`.
   - Uses generic `TypeVar` annotations instead of importing contracts from higher layers.

### Domain

3. **`contract` (Domain Layer)**:
   - Depends strictly on `config` (exceptions, settings, enums) and standard library primitives (`abc`, `typing`).
   - Defines pure abstractions (`ABC`), protocol state machines, and session context boundaries.
   - Zero dependencies on `util`, concrete implementation packages, presentation, or external plugins.

### Application

4. **`command` (Command Operations)**:
   - Depends on `contract` and foundation layers.
   - Encapsulates discrete executable operations via immutable, self-validating DTOs.
   - Fully decoupled from runtime transport mechanics and operator terminal I/O.
5. **`controller` (Application Handlers)**:
   - Depends on `contract` and `command`.
   - Thin application handlers that parse requests, construct command DTOs, and coordinate dispatching.
   - Emits structured lifecycle signals instead of control-flow exceptions.

### Infrastructure

6. **`core` (Infrastructure Services)**:
   - Implements infrastructure contracts defined in `contract` (CLI parser, routing, plugin registry).
   - Manages dynamic multi-tier plugin discovery and enforces contract validation barriers.
   - Operates strictly on plugin abstractions with zero knowledge of concrete transport packages.

### Presentation

7. **`presentation` (User Interface & Delivery)**:
   - Depends on `contract` and foundation layers.
   - Manages interactive terminal REPL loops, readline history, and stream formatting.
   - Communicates with the application layer exclusively through route dispatching and lifecycle signals.

### Composition Root

8. **`main` (Composition Root)**:
   - The sole layer aware of all system components.
   - Discovers plugins, wires routers, injects dependencies, and bootstraps application lifecycles.
   - Traps unhandled errors, displays user-friendly diagnostics, and maps to deterministic exit codes.

### Ecosystem & Verification

9. **`plugins` (Autonomous Packages)**:
   - Independent, self-contained packages residing outside the core application loop.
   - Strictly implement domain contracts.
   - Bundle their own isolated stager templates, helper libraries, and colocated test suites.
10. **`testing` (Public Testing SDK)**:
    - Published test harness supplying deterministic, fully-typed test doubles and fixtures.
    - Provides reusable conformance suites to verify contract invariants.
    - Replaces unconstrained `MagicMock` sprawl with contract-compliant in-memory implementations.

## Development Setup

### Prerequisites

- **Python 3.11+**
- **uv** (recommended high-performance package and project manager)
- **Make** (GNU Make for standardized execution workflows)
- **Pytest** (test suite runner and assertion harness)
- **Mypy** (strict static type analysis)
- **Ruff** (high-speed linter and code formatter)

### Setting up the Environment

```bash
# Clone the repository
git clone https://github.com/othonhugo/declusor.git
cd declusor

# Option A: Fast setup using uv (Recommended)
make install

# Option B: Manual setup using python3 venv + pip
python3 -m venv .venv

source .venv/bin/activate

pip install -e ".[dev,testing]"
pip install -e plugins/shell_socket
pip install -e plugins/py_socket
```

## Coding Standards & Invariants

### Namespace Imports & Typing Discipline

Always import external package namespaces directly rather than destructuring individual symbols across layers.

However, never import the namespace of the package the code itself resides in—within the same package, deconstruct internal modules using relative imports:

```python
# CORRECT: Clean namespace qualification for external packages
from declusor import command, config, contract, core, presentation, util

session = contract.SessionContext(...)
cmd = command.ExecuteCommand(dto)

# CORRECT: Deconstruct when inside the same package (e.g. inside declusor/contract/)
from .state import ConnectionState
from .session import SessionContext
```

```python
# FORBIDDEN: Importing own package namespace from within that package
# (e.g. inside src/declusor/contract/plugin.py)
from declusor import contract
class MyPlugin(contract.IPlugin): ...

# FORBIDDEN: Destructuring separated symbols across external layers
from declusor.testing import DummyConsole, DummyConnection
from declusor.presentation import PromptCLI
from declusor.main.app import Application
```

#### Type Hints & `TYPE_CHECKING`

Always guard imports under `if TYPE_CHECKING:` when symbols or types are required **exclusively for type annotations/hints** to prevent circular dependencies and unnecessary runtime overhead:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse
    from declusor import contract
```

### Exception Re-exports

Each subpackage re-exports its respective domain exceptions from `declusor.config` within its `__init__.py` and in `__all__`.

When handling or raising layer-specific errors, consumers can import them directly from the relevant package namespace (e.g. `core.ParserError`, `command.CommandError`).

### Docstring Rhythm (Blank Line Separation)

Never glue docstrings directly to executable code. Always insert exactly one blank line between the closing triple quotes (`"""`) of a docstring and the first line of code inside functions, methods, and nested controllers:

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

### Package README Documentation

Every package directory must maintain a `README.md` containing at least:

1. `# <Package Name>`: Top-level section with the package name followed by a concise description of the package's role, dependencies, and architectural context.
2. `## Modules`: A markdown table with columns `Module` and `Responsibility` documenting every module in the package without empty rows.
3. `## Design Principles`: A numbered list detailing the design rationale and architectural guarantees of that layer.

### Strict Static Typing

- All production and test code must carry complete, precise type annotations.
- `mypy src plugins tests` must pass with zero errors under `--strict`.
- Never use untyped `Any` where a generic `TypeVar`, `Protocol`, or explicit union can be defined.

## Testing Guidelines

### Mock-Free Deterministic Test Doubles

Do **not** use unconstrained `unittest.mock.MagicMock` or fragile monkeypatching to satisfy core contracts. Use the typed doubles provided by `declusor.testing`.

Standard pytest fixtures are pre-registered via `pytest_plugins = ["declusor.testing.pytest_plugin"]`.

### Colocated Plugin Tests & Conformance

Native plugin tests live inside `plugins/<plugin_name>/tests/`.

Every client plugin must implement contract conformance tests by inheriting from `testing.PluginConformanceTestSuite`:

```python
from declusor import testing
from declusor_my_plugin import MyPlugin


class TestMyPluginConformance(testing.PluginConformanceTestSuite):
    plugin_class = MyPlugin
```

## Plugin Authoring Guide

All plugins must follow the autonomous package layout:

```text
plugins/<plugin_name>/
├── pyproject.toml               # Standalone package metadata & entry point
├── README.md                    # Plugin documentation
├── src/
│   └── declusor_<plugin_name>/
│       ├── __init__.py          # Exports: __all__ = ["<PluginClass>"]
│       ├── plugin.py            # Implements IPlugin & IPluginRuntime
│       └── connection.py        # Implements IConnection, IConnectionProfile & IClientFileStore
├── assets/                      # Bundled stagers and libraries
│   ├── launchers/               # Bootstrap stagers
│   ├── helpers/                 # Library files sent during session handshake
│   └── modules/                 # On-demand discovery/execution modules
└── tests/                       # Dedicated unit & conformance test suite
    ├── conftest.py
    └── test_conformance.py
```

### Entry Point Declaration

Register the plugin in `plugins/<plugin_name>/pyproject.toml`:

```toml
[project]
name = "declusor-<plugin_name>"
version = "<major>.<minor>.<patch>"
dependencies = ["declusor>=0.3.1"]

[project.entry-points."declusor.plugins"]
<plugin_name> = "declusor_<plugin_name>:<PluginClass>"
```

## Verification & Quality Gates

Before opening a pull request or submitting code, ensure that all quality gates pass using the project `Makefile`:

```bash
# Run the complete verification suite (formatting check, linting, strict mypy, and tests)
make check

# Granular verification targets
make format-check                       # Verify code formatting with Ruff
make format                             # Automatically format code and apply safe fixes
make lint                               # Run Ruff linter checks
make type-check                         # Run Mypy strict type analysis across host and plugins
make test                               # Run all unit, integration, and conformance tests
make compile                            # Verify bytecode compilation across src, tests, and plugins

# Plugin verification targets
make check-plugin PLUGIN=<plugin_name>  # Full check for a specific plugin
make test-plugin PLUGIN=<plugin_name>   # Run tests for a specific plugin
make test-plugins                       # Run tests across all plugins
```

## Git Workflow & Commit Guidelines

### Branching Strategy

Create dedicated topic branches from `main` using descriptive prefix naming:

- `feat/<feature-name>`: New capabilities or functional additions
- `fix/<bug-name>`: Defect repairs or bug resolutions
- `refactor/<target>`: Structural code improvements preserving behavior
- `test/<target>`: Test doubles, conformance suites, or coverage additions
- `docs/<topic>`: Documentation, architectural guides, or specification updates

### Conventional Commits

Commit messages must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```text
<type>(<scope>): <summary in imperative mood, lower-case>

[optional body explaining non-obvious architectural choices or rationale]

[optional footer(s), e.g. BREAKING CHANGE or issue references]
```

- **Types**: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
- **Scopes**: Must align with architectural boundaries: `contract`, `core`, `presentation`, `controller`, `command`, `config`, `util`, `plugins`, `testing`, `main`
- **Summary**: Concise, imperative, present-tense without trailing periods (e.g. "add", "refactor", "enforce", not "added" or "adds")

#### Examples

- `feat(plugins): standardize autonomous plugin packages with src-layout and entry points`
- `refactor(contract): decouple domain interfaces from stateless util primitives`
- `fix(core): reject unregistered plugin commands during CLI parse phase`
- `test(py_socket): add conformance suite verification against IPlugin contracts`
- `docs(contributing): clarify namespace import invariants and TYPE_CHECKING guardrails`

### Pull Request Expectations

Every pull request submitted to Declusor must adhere to the following principles:

1. **Focused Scope & Atomic Changes**:
   - Keep pull requests small and focused on a single concern, feature, or bug fix.
   - Avoid bundling unrelated refactorings or cosmetic cleanups into feature branches.

2. **Architectural & Invariant Compliance**:
   - Respect strict unidirectional dependency flow across all architectural boundaries (`Foundations`, `Domain`, `Application`, `Infrastructure`, `Presentation`, `Composition Root`).
   - Honor namespace import rules: never import the package's own namespace internally, and guard hint-only dependencies with `if TYPE_CHECKING:`.

3. **Rigorous Test Coverage & Quality Gates**:
   - Accompany new features, bug fixes, and plugin additions with dedicated tests.
   - Use reusable test doubles from `testing` rather than uncontrolled `MagicMock` patches.
   - For transport plugins, implement and pass the `PluginConformanceTestSuite`.
   - Ensure the entire verification gate (`make check`) passes with zero warnings or errors.

4. **Self-Documenting Context & Clarity**:
   - Provide a clear PR description explaining the **why** behind changes, architectural trade-offs, and verification commands executed.
   - Update relevant documentation (`README.md`, layer guides, or API docstrings) in lockstep with code modifications.

### Pre-Submission Checklist

Before opening or requesting review on a pull request:

- [ ] `make check` executes cleanly (code formatting, Ruff linting, strict Mypy, and 100% test suite pass).
- [ ] New components strictly conform to their layer's dependency and import invariants.
- [ ] Any added or modified plugin passes `PluginConformanceTestSuite`.
- [ ] Commit history is cleanly rebased against `main` and strictly follows Conventional Commits.
- [ ] Documentation and inline docstrings (with proper blank line rhythm) are updated.
