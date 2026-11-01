# `shell_socket` plugin

## Overview

`shell_socket` provides a lightweight POSIX shell client for Declusor
sessions. It uses Bash's `/dev/tcp` support and does not require `nc`,
`socat`, Python, or other external target-side tools.

## Capabilities

- Native Bash socket transport for Linux and compatible POSIX environments.
- In-memory bootstrap and helper delivery.
- Ephemeral per-command delimiters for streamed output.
- Command execution, code/module operations, uploads, and interactive shells.

## Compatibility

| Component | Supported environment |
| --- | --- |
| Host plugin source | Python 3.12+ |
| Remote client asset | Bash with `/dev/tcp` support |
| Transport | TCP |

## Installation

Install the main project and the plugin in editable mode:

```bash
make install
```

Or install this package directly:

```bash
python -m pip install -e plugins/shell_socket
```

## Quick start

```bash
declusor 127.0.0.1 4444 --plugin shell_socket
```

The listener prints the launcher required to establish the remote session.
Use the main [Declusor README](../../README.md) for session commands and
launcher delivery options.

## Protocol

The wire protocol uses ephemeral envelopes over a Bash `/dev/tcp` stream.
See [PROTOCOL.md](PROTOCOL.md) for framing, delimiter generation, handshake,
and session lifecycle details.

## Package layout

| Path | Responsibility |
| --- | --- |
| `src/declusor_shell_socket/plugin.py` | Plugin registration, runtime, and asset processing |
| `src/declusor_shell_socket/connection.py` | Connection and stream I/O |
| `src/declusor_shell_socket/renderer.py` | Operation rendering |
| `assets/launchers/` | Remote bootstrap and client payloads |
| `assets/helpers/` | Remote helper scripts |
| `assets/modules/` | Optional remote modules |

## Development and validation

Run the plugin checks from the repository root:

```bash
make check TARGET=plugins PLUGIN=shell_socket
make check TARGET=plugin-assets PLUGIN=shell_socket
```

The asset check validates Python asset syntax and runs ShellCheck over shell
assets. Install ShellCheck locally when it is not already available.

## Limitations

- The target must provide Bash and `/dev/tcp` support.
- This plugin is not intended for generic `/bin/sh` implementations without
  the required Bash features.
- TCP sessions are not encrypted by this plugin.
- Remote command execution must only be used on systems where authorization
  has been obtained.

## License

See the repository [LICENSE](../../LICENSE).
