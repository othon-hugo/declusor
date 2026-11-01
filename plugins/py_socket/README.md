# Python Socket Plugin (`py_socket`)

The `py_socket` plugin provides a cross-platform reverse-shell client capable of executing payloads directly in-memory or delegating to the operating system shell. The agent is implemented in pure Python (standard library only), ensuring seamless execution across Linux, macOS, and Windows.

For detailed specification of [...], see [PROTOCOL.md](PROTOCOL.md).

## Modules

| Module       | Responsibility                                                                                                        |
| ------------ | --------------------------------------------------------------------------------------------------------------------- |
| `connection` | Python socket connection transport (`PySocketConnection`) and operation renderer (`PySocketRenderer`)                 |
| `plugin`     | Entry-point plugin (`PySocketPlugin`), runtime adapter (`PySocketRuntime`), and asset processor (`PySocketProcessor`) |
| `renderer`   |                                                                                                                       |
