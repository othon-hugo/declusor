# Declusor Plugins

This directory houses the built-in client plugins distributed with Declusor. Because Declusor employs a dynamic, multi-tier discovery architecture, third-party developers can create, test, and distribute custom plugins using the exact same structure.

## Plugin Architecture & Contracts

Every plugin is an autonomous package that implements the contracts defined in `declusor.contract`:

| Contract             | Responsibility                                                                          |
| -------------------- | --------------------------------------------------------------------------------------- |
| `IClientPlugin`      | Registers CLI flags, parses options, validates configuration, and builds the runtime.   |
| `IClientRuntime`     | Renders the bootstrap script and instantiates the `IConnection` for an accepted socket. |
| `IConnection`        | Manages the framed read/write protocol and lifecycle state (`ConnectionState`).         |
| `IClientFileStore`   | Loads initialization helpers, bootstrap scripts, and on-demand discovery modules.       |
| `IConnectionProfile` | Holds timeouts, buffer sizes, and operation templates (`EXEC_FILE`, `STORE_FILE`).      |

## How Plugins are Discovered

Declusor discovers plugins at runtime across **three tiers**:

1. **Repository / Built-in Plugins** (`plugins/` directory):

   All valid subdirectories in `plugins/` that implement `IClientPlugin` are automatically discovered on startup.

2. **Python Entry Points** (PEP 621):

   External plugins installed via `pip` declare the `declusor.plugins` entry point group:

   ```toml
   [project.entry-points."declusor.plugins"]
   declusor_plugin = "declusor_plugin:DeclusorPlugin"
   ```

3. **Drop-in Directories**:

   Plugins placed in `~/.declusor/plugins/` or specified via the `--plugin-dir` CLI option are dynamically loaded via `importlib`.

**Precedence Order**: Custom CLI (`--plugin-dir`) > User drop-in (`~/.declusor/plugins`) > Entry points (pip) > Built-in (`plugins/`).

## Creating a Custom Plugin

### 1. Create the Plugin Structure

```bash
mkdir -p my_client/src/declusor_my_client
mkdir -p my_client/assets/{launchers,helpers,modules}
mkdir -p my_client/tests
touch my_client/pyproject.toml my_client/README.md
touch my_client/src/declusor_my_client/{__init__.py,plugin.py,connection.py}
```

Canonical layout:

```text
my_client/
├── pyproject.toml     # Standalone package metadata & entry point
├── README.md          # Plugin documentation
├── src/
│   └── declusor_my_client/
│       ├── __init__.py    # Exports
│       ├── plugin.py      # IClientPlugin implementation
│       └── connection.py  # IConnection & IClientFileStore implementation
├── assets/            # Bundled stagers and libraries
│   ├── launchers/
│   ├── helpers/
│   └── modules/
└── tests/             # Contract conformance and unit tests
    └── test_conformance.py
```

### 2. Implement the Contracts

In `my_client/src/declusor_my_client/plugin.py`:

```python
from pathlib import Path
from declusor import contract, util, config


class MyClientPlugin(contract.IClientPlugin):
    name = "my_client"
    description = "Description of my custom client"
    version = "1.0.0"

    @classmethod
    def configure_parser(cls, parser: util.Parser, /) -> None:
        parser.add_argument("--my-option", help="Custom option for this client")

    @classmethod
    def build_config(cls, args: util.Namespace, data_paths: config.DataPaths | None = None, /) -> contract.ClientConfig:
        return contract.ClientConfig(
            kind=cls.name,
            host=args.host,
            port=args.port,
            options={"my_option": getattr(args, "my_option", None)},
        )

    @classmethod
    def validate(cls, client_config: contract.ClientConfig, /) -> None:
        pass

    @classmethod
    def build_runtime(cls, client_config: contract.ClientConfig, /) -> contract.IClientRuntime:
        return MyClientRuntime(client_config)
```

### 3. Verify Contract Conformance with `declusor.testing`

Plugin authors can use Declusor's built-in testing SDK to verify compliance:

```python
import pytest
from declusor import contract
from declusor.testing import PluginConformanceTestSuite
from declusor_my_client.plugin import MyClientPlugin


class TestMyClientConformance(PluginConformanceTestSuite):
    @pytest.fixture
    def plugin_class(self) -> type[contract.IClientPlugin]:
        return MyClientPlugin
```

Execute verification using `make`:

```bash
make test-plugin PLUGIN=my_client
```

### 4. Test Live with Declusor

Run Declusor pointing to your plugin directory:

```bash
declusor 0.0.0.0 9000 --client my_client --plugin-dir /path/to/my_client_parent_dir
```
