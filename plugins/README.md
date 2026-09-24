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
   my_plugin = "my_plugin_package:MyPluginClass"
   ```

3. **Drop-in Directories**:

   Plugins placed in `~/.declusor/plugins/` or specified via the `--plugin-dir` CLI option are dynamically loaded via `importlib`.

**Precedence Order**: Custom CLI (`--plugin-dir`) > User drop-in (`~/.declusor/plugins`) > Entry points (pip) > Built-in (`plugins/`).

## Creating a Custom Plugin

### 1. Create a Package Directory

```bash
mkdir -p my_client/assets/{launchers,helpers,modules}
touch my_client/{__init__.py,plugin.py,connection.py,README.md}
```

### 2. Implement the Contracts

In `my_client/plugin.py`:

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

### 3. Test with Declusor

Run Declusor pointing to your plugin directory:

```bash
declusor 0.0.0.0 9000 --client my_client --plugin-dir /path/to/my_client_parent_dir
```
