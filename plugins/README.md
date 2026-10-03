# Declusor Plugins

This directory houses the built-in client plugins distributed with Declusor. Because Declusor employs a dynamic, multi-tier discovery architecture, third-party developers can create, test, and distribute custom plugins using the exact same structure.

## Plugin Architecture & Contracts

Every plugin is an autonomous package that implements the contracts defined in `declusor.contract`:

| Contract             | Responsibility                                                                                       |
| -------------------- | ---------------------------------------------------------------------------------------------------- |
| `IPluginExtension`   | Registers CLI flags, parses options, validates configuration, and builds the runtime.                |
| `IPluginRuntime`     | Produces `LauncherDelivery` and instantiates the `IConnection` for an accepted socket.               |
| `IConnection`        | Manages the framed read/write protocol and lifecycle state (`ConnectionState`).                      |
| `IPluginProcessor`   | Loads initialization helpers, bootstrap templates, and on-demand discovery modules.                  |
| `IConnectionProfile` | Holds timeouts, buffer sizes, and operation templates (`EXEC_FILE`, `STORE_FILE`, `LOAD_MODULE`).    |

## How Plugins are Discovered

Declusor discovers plugins at runtime across **three tiers**:

1. **Repository / Built-in Plugins** (`plugins/` directory):

   All valid subdirectories in `plugins/` that implement `IPluginExtension` are automatically discovered on startup.

2. **Python Entry Points** (PEP 621):

   External plugins installed via `pip` declare the `declusor.plugins` entry point group:

   ```toml
   [project.entry-points."declusor.plugins"]
   my_plugin = "declusor_my_plugin:MyPlugin"
   ```

3. **Drop-in Directories**:

   Plugins placed in `~/.declusor/plugins/` or specified via the `--plugin-dir` CLI option are dynamically loaded via `importlib`.

**Precedence Order**: Custom CLI (`--plugin-dir`) > User drop-in (`~/.declusor/plugins`) > Entry points (pip) > Built-in (`plugins/`).

## Creating a Custom Plugin

### 1. Create the Plugin Structure

```bash
mkdir -p my_plugin/src/declusor_my_plugin
mkdir -p my_plugin/assets/{launchers,helpers,modules}
mkdir -p my_plugin/tests
touch my_plugin/pyproject.toml my_plugin/README.md
touch my_plugin/src/declusor_my_plugin/{__init__.py,plugin.py,connection.py}
```

Canonical layout:

```text
my_plugin/
├── pyproject.toml            # Standalone package metadata & entry point
├── README.md                 # Plugin documentation
├── src/
│   └── declusor_my_plugin/
│       ├── __init__.py       # Exports
│       ├── plugin.py         # IPluginExtension, IPluginRuntime, and IPluginProcessor
│       └── connection.py     # IConnection and IConnectionProfile implementation
├── assets/                   # Bundled stagers and libraries
│   ├── launchers/
│   ├── helpers/
│   └── modules/
└── tests/                    # Contract conformance and unit tests
    └── test_conformance.py
```

### 2. Implement the Contracts

In `my_plugin/src/declusor_my_plugin/plugin.py`:

```python
from collections.abc import Mapping
from pathlib import Path

from declusor import config, contract


class MyOptions(contract.ParsedArguments, total=False):
    my_option: str | None


class MyPlugin(contract.IPluginExtension[MyOptions]):
    name = "my_plugin"
    description = "Description of my custom client"
    version = "1.0.0"
    options_type = MyOptions

    @classmethod
    def configure_parser(cls, parser: contract.IArgumentParser, /) -> None:
        parser.add_argument("--my-option", help="Custom option for this client")

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> MyOptions:
        opt = raw.get("my_option")
        return MyOptions(my_option=str(opt) if opt is not None else None)

    @classmethod
    def build_config(
        cls,
        host: str,
        port: int,
        options: MyOptions,
        /,
        filesystem: contract.PluginFilesystem | None = None,
        mode: config.ExecutionMode = config.DEFAULT_EXECUTION_MODE,
    ) -> contract.PluginConfig[MyOptions]:
        resolved_fs = filesystem or contract.PluginFilesystem.from_root(Path(__file__).parents[2])

        return contract.PluginConfig(
            kind=cls.name,
            host=host,
            port=port,
            options=options,
            options_type=cls.options_type,
            filesystem=resolved_fs,
            mode=mode,
        )

    @classmethod
    def validate(cls, plugin_config: contract.PluginConfig[MyOptions], /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config: contract.PluginConfig[MyOptions], /) -> contract.IPluginRuntime:
        return MyRuntime(plugin_config)
```

### 3. Verify Contract Conformance with `declusor.testing`

Plugin authors can use Declusor's built-in testing SDK to verify compliance:

```python
import pytest
from declusor import contract, testing
from declusor_my_plugin.plugin import MyOptions, MyPlugin


class TestMyPluginConformance(testing.PluginConformanceTestSuite[MyOptions]):
    @pytest.fixture
    def plugin_class(self) -> type[contract.IPluginExtension[MyOptions]]:
        return MyPlugin
```

Execute verification using `make`:

```bash
make check-plugin PLUGIN=my_plugin  # Full quality check (format, lint, strict mypy, tests)
make test-plugin PLUGIN=my_plugin   # Run dedicated unit and conformance tests
```

### 4. Test Live with Declusor

Run Declusor pointing to your plugin directory:

```bash
declusor 0.0.0.0 9000 --plugin my_plugin --plugin-dir /path/to/my_plugin
```
