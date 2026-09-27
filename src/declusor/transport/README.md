# Transport Package

The **transport** package provides concrete implementations of the transport abstractions defined in `declusor.contract.transport`. It encapsulates physical network byte-stream I/O (TCP sockets, listeners) and composable stream obfuscation / encryption decorators, completely isolating low-level OS networking mechanics from session-layer protocols.

> [!NOTE]
> This package depends only on `config`, `contract`, and `util`. It has zero dependencies on `core`, `command`, `controller`, `presentation`, `main`, or external `plugins`.

## Modules

| Module     | Responsibility                                                                         |
| :--------- | :------------------------------------------------------------------------------------- |
| `listener` | TCP server listener (`TcpListener`) binding network addresses and accepting transports |
| `socket`   | Connected TCP socket transport (`SocketTransport`) with fail-fast exception mapping    |
| `xor`      | Repeating-key stream cipher decorator (`XorTransport`) resilient to TCP fragmentation  |

## Design Principles

1. **Clean Exception Translation** — low-level OS networking errors (`BrokenPipeError`, `ConnectionResetError`, `TimeoutError`, `socket.error`) are deterministically caught and translated into domain exceptions (`ConnectionClosed`, `ConnectionTimeoutError`, `ConnectionError`).
2. **Pure Interface Composition** — decorators such as `XorTransport` directly implement `ITransport` and wrap an underlying `ITransport`, avoiding deep inheritance trees.
3. **Stream Segmentation Immunity** — stream ciphers track independent egress (`_write_offset`) and ingress (`_read_offset`) cursors, ensuring that arbitrary TCP packet fragmentation never corrupts or desynchronizes communications.
4. **Idempotent Resource Management** — all transports and listeners provide idempotent `close()` methods and full context manager (`with`) support.
