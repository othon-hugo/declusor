# Python Socket Plugin (`py_socket`)

The `py_socket` plugin provides a cross-platform Python-based reverse-shell client capable of executing payloads directly in-memory or delegating to the operating system shell.

## Overview

- **Identifier**: `py_socket`
- **Target OS**: Cross-platform (Linux, macOS, Windows)
- **Dependencies on Target**: Standard Python 3.6+ (zero external pip packages)
- **Execution Engine**: Dual-mode (in-memory `exec()` for Python code and helper calls; `subprocess.Popen` for system commands)

## Package Structure

```text
plugins/py_socket/
├── __init__.py        # Public package exports
├── plugin.py          # PySocketPlugin (IClientPlugin) & PySocketRuntime (IClientRuntime)
├── connection.py      # PySocketConnection (IConnection) & PySocketFileStore
├── README.md          # This documentation
└── assets/            # Bundled stagers and libraries
    ├── launchers/     # py_socket_client.py (self-contained agent)
    ├── helpers/       # file.py, util.py (initialization bundle)
    └── modules/       # discovery/dev_tools.py, discovery/system_info.py
```

## How It Works

1. **Bootstrap**: When launched, `PySocketRuntime` renders `assets/launchers/py_socket_client.py` substituting `$HOST`, `$PORT`, and `$ACKNOWLEDGE`.
2. **Handshake**: The client connects, receives the concatenated Python helpers (`helpers/file.py`, `helpers/util.py`), executes them into a persistent `_SESSION_SCOPE` dictionary, and sends back the SHA-256 ACK.
3. **Execution**:
   - Python code / helper calls: executed via `exec(payload, _SESSION_SCOPE)` capturing `sys.stdout` and `sys.stderr`.
   - Shell commands: executed via `subprocess.Popen(payload, shell=True)` streaming output.
