# Shell Socket Plugin (`shell_socket`)

The `shell_socket` plugin provides a lightweight, zero-dependency reverse-shell client using Linux's native `/dev/tcp` virtual file descriptor interface. It establishes an interactive bidirectional connection directly through Bash, requiring no external tools (such as `nc`, `socat`, or Python) on the target host.

For detailed specification of wire framing, nonces, and session transitions, see [PROTOCOL.md](PROTOCOL.md).

## Modules

| Module       | Responsibility                                                                                                                 |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| `connection` | Reverse-shell connection transport (`ShellSocketConnection`) and operation renderer (`ShellSocketRenderer`)                    |
| `plugin`     | Entry-point plugin (`ShellSocketPlugin`), runtime adapter (`ShellSocketRuntime`), and asset processor (`ShellSocketProcessor`) |
| `renderer`   |                                                                                                                                |
