# Shell Socket Plugin (`shell_socket`)

The `shell_socket` plugin provides a lightweight, zero-dependency reverse-shell client using Linux's native `/dev/tcp` virtual file descriptor interface.

## Modules

| Module       | Responsibility                                                             |
| ------------ | -------------------------------------------------------------------------- |
| `connection` | Reverse-shell connection transport, protocol profile, and asset file store |
| `plugin`     | Entry-point plugin class (`IClientPlugin`) and runtime orchestrator        |

## Design Principles

1. **Zero External Dependencies** — relies entirely on Python stdlib and Linux `/dev/tcp` virtual files.
2. **Contract Conformance** — strictly implements `IClientPlugin`, `IClientRuntime`, and `IConnection`.
3. **Deterministic Framing** — uses null-delimited commands and SHA-256 segmented ACK stream markers.
4. **Idempotent Lifecycle** — ensures safe multiple closes and clean disconnection transitions.
