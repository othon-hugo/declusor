---
name: declusor-plugin-development
description: Guide for developing, structuring, configuring, and verifying autonomous client transport plugins for Declusor. Use when creating a new plugin, refactoring existing plugins, or adding conformance tests.
---

# Declusor Plugin Development Guide

This skill details how to author, package, and verify autonomous client plugins for Declusor.

## 1. Plugin Directory Layout

Every plugin must be an autonomous package situated in `plugins/<plugin_name>/`:

```text
plugins/<plugin_name>/
├── pyproject.toml         # Standalone package definition
├── README.md              # Documentation with ## Modules and ## Design Principles
├── src/
│   └── declusor_<plugin_name>/
│       ├── __init__.py    # Public exports (__all__ = ["<PluginClass>"])
│       ├── plugin.py      # Implements IPlugin & IPluginRuntime
│       └── connection.py  # Implements IConnection, IConnectionProfile, IClientFileStore
├── assets/
│   ├── launchers/         # Bootstrap stagers (e.g. client.py, client.sh)
│   ├── helpers/           # Library files sent during session handshake
│   └── modules/           # On-demand discovery/execution modules
└── tests/
    ├── conftest.py
    └── test_conformance.py # PluginConformanceTestSuite inheritance
```

## 2. Manifest Configuration (`pyproject.toml`)

Configure `pyproject.toml` with the entry point under group `declusor.plugins`:

```toml
[project]
name = "declusor-<plugin_name>"
version = "<major>.<minor>.<patch>"
description = "<plugin description>"
readme = "README.md"
requires-python = ">=3.11,<4.0"
dependencies = [
    "declusor>=0.3.1",
]

[project.entry-points."declusor.plugins"]
<plugin_name> = "declusor_<plugin_name>:<PluginClass>"
```

## 3. Implementing Core Interfaces

Plugins implement contracts defined in `declusor.contract`:

1. **`IPlugin`**:
   - `name: str`: Unique identifier matching the entry point key.
   - `description: str`, `version: str`: Metadata.
   - `configure_parser(parser: IArgumentParser) -> None`: Registers plugin-specific CLI flags.
   - `build_config(args: PluginArguments, data_paths: DataPaths) -> PluginConfig`: Constructs validated configuration.
   - `validate(plugin_config: PluginConfig) -> None`: Validates assets and pre-conditions.
   - `build_runtime(plugin_config: PluginConfig) -> IPluginRuntime`: Instantiates runtime.
2. **`IPluginRuntime`**:
   - `client_files: IClientFileStore`: Exposes file store.
   - `client_script: str`: Returns rendered stager code.
   - `create_connection(connection: socket) -> IConnection`: Wraps raw socket in transport connection.
3. **`IConnection`**:
   - Manages state lifecycle: `ConnectionState.CREATED` -> `CONNECTED` -> `CLOSED`.
   - Idempotent `close()`.
   - Streaming `read() -> Iterator[bytes]` and `write(data: bytes) -> None`.

## 4. Contract Conformance Testing

Always inherit from `PluginConformanceTestSuite` to automatically verify all contract invariants:

```python
from declusor import testing
from declusor_my_plugin import MyPlugin


class TestMyPluginConformance(testing.PluginConformanceTestSuite):
    plugin_class = MyPlugin
```

## 5. Verification Commands

Targeted verification for plugins is executed using `make`:

```bash
# Run all quality checks for a specific plugin (format-check, lint, type-check, test)
make check-plugin PLUGIN=<plugin_name>

# Granular plugin targets
make test-plugin PLUGIN=<plugin_name>         # Run unit and conformance tests
make type-check-plugin PLUGIN=<plugin_name>   # Strict mypy static analysis
make lint-plugin PLUGIN=<plugin_name>         # Ruff linter validation
make format-check-plugin PLUGIN=<plugin_name> # Code formatting validation
make format-plugin PLUGIN=<plugin_name>       # Auto-format and fix

# Run tests across all plugins
make test-plugins
```
