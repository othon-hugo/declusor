# Shell Socket Plugin (`shell_socket`)

The `shell_socket` plugin provides a lightweight, zero-dependency reverse-shell client using Linux's native `/dev/tcp` virtual file descriptor interface.

## Overview

- **Identifier**: `shell_socket`
- **Target OS**: Linux / POSIX systems with Bash
- **Dependencies on Target**: None (uses built-in `/dev/tcp`)
- **Transport**: Raw TCP socket with null-delimited request framing and SHA-256 ACK streaming

## Package Structure

```text
plugins/shell_socket/
├── __init__.py        # Public package exports
├── plugin.py          # ShellSocketPlugin (IClientPlugin) & ShellSocketRuntime (IClientRuntime)
├── connection.py      # ShellSocketConnection (IConnection) & ShellSocketFileStore
├── README.md          # This documentation
└── assets/            # Bundled stagers and libraries
    ├── launchers/     # shell_socket_client.sh (one-line stager)
    ├── helpers/       # file.sh, util.sh (initialization bundle)
    └── modules/       # discovery/*.sh (on-demand modules)
```

## How It Works

1. **Bootstrap**: When launched, `ShellSocketRuntime` renders `assets/launchers/shell_socket_client.sh` with the server's IP, port, and expected client ACK seed.
2. **Handshake**: The server transmits all concatenated helpers from `assets/helpers/` (`file.sh`, `util.sh`). The remote client executes them in memory and responds with its 32-byte SHA-256 ACK.
3. **Execution**: Subsequent commands (`command`, `execute`, `upload`, `load`, `shell`) are framed with `\0` and output streamed back until the ACK sentinel.
