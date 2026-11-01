# `py_socket` plugin

`py_socket` provides a cross-platform Python client for Declusor sessions. The plugin uses only the Python standard library and supports in-memory staging, framed command execution, file transfers, and interactive shell operations.

The host-side implementation in `src/declusor_py_socket` follows the current Declusor Python requirement (Python 3.12+). The files under `assets/` are independent payloads delivered to remote targets and intentionally preserve their documented older-runtime compatibility.

## Capabilities

- Python socket transport for Linux, macOS, and Windows targets.
- Chunked TLV framing with separate output, error, control, and exit channels.
- In-memory client bootstrap and helper/module delivery.
- Command execution, code evaluation, uploads, and interactive shells.

## Compatibility

| Component           | Supported environment                          |
| ------------------- | ---------------------------------------------- |
| Host plugin source  | Python 3.12+                                   |
| Remote client asset | Python runtime supported by the selected asset |
| Transport           | TCP                                            |

## Installation

Install the main project and the plugin in editable mode:

```bash
make install
```

Or install this package directly:

```bash
python -m pip install -e plugins/py_socket
```

## Quick start

```bash
declusor 127.0.0.1 4444 --plugin py_socket
```

The listener prints the launcher required to establish the remote session. Use the main [Declusor README](../../README.md) for session commands and launcher delivery options.

## Protocol

The wire protocol uses chunked TLV frames over TCP. See [PROTOCOL.md](PROTOCOL.md) for the frame layout, channels, handshake, and session lifecycle.

## Package layout

| Path                                   | Responsibility                                     |
| -------------------------------------- | -------------------------------------------------- |
| `src/declusor_py_socket/plugin.py`     | Plugin registration, runtime, and asset processing |
| `src/declusor_py_socket/connection.py` | Connection and framed I/O                          |
| `src/declusor_py_socket/renderer.py`   | Operation rendering                                |
| `assets/launchers/`                    | Remote bootstrap and client payloads               |
| `assets/helpers/`                      | Remote helper modules                              |
| `assets/modules/`                      | Optional remote discovery modules                  |

## Development and validation

Run the plugin checks from the repository root:

```bash
make check TARGET=plugins PLUGIN=py_socket
make check TARGET=plugin-assets PLUGIN=py_socket
```

The asset check validates Python asset syntax without applying the host plugin's type-checking rules.

## Limitations

- The target must provide a compatible Python interpreter for the selected launcher.
- TCP sessions are not encrypted by this plugin.
- Remote command execution must only be used on systems where authorization has been obtained.

## License

See the repository [LICENSE](../../LICENSE).
