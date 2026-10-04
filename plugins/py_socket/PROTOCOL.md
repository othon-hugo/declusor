# Declusor `py_socket` Protocol Specification

This document specifies the wire protocol, framing format, channel multiplexing, and session lifecycle for the `py_socket` transport plugin in Declusor.

## Protocol Architecture & Framing Mode

The `py_socket` plugin implements the **`FramingMode.CHUNKED_TLV`** (Type-Length-Value) protocol over raw TCP byte streams.

Unlike sentinel-based protocols that scan for byte sequences or delimiters in the stream, `CHUNKED_TLV` frames data with deterministic prefix headers. This achieves:

- **Zero Delimiter Collision**: Any arbitrary byte sequence (including null bytes `\x00`, newlines, or binary blobs) can be transmitted safely without escape sequences ($P(\text{collision}) = 0$).
- **Zero Trailing Latency**: Chunks are yielded immediately upon reading their declared length, eliminating the need to buffer $k$ bytes in reserve.
- **Multiplexed Channels**: Distinct data channels (stdout, stderr, control signals, process exit code) share the same underlying stream.
- **Process Exit Propagation**: Child process termination status (`$?` / `returncode`) is communicated natively to the server.

## Binary Frame Layout

Every frame on the wire consists of a **5-byte fixed header** followed by a variable-length payload:

```text
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+---------------+-----------------------------------------------+
|  Channel (1B) |                 Length (4B)                   |
+---------------+-----------------------------------------------+
|                         Payload ...                           |
|                    (Length bytes total)                       |
+---------------------------------------------------------------+
```

### Header Fields

| Field              |        Type        | Encoding | Description                                              |
| :----------------- | :----------------: | :------: | :------------------------------------------------------- |
| **Channel ID**     |  1 byte (`uint8`)  |   `>B`   | Identifies the payload type and handling channel.        |
| **Payload Length** | 4 bytes (`uint32`) |   `>I`   | Length of the payload in bytes ($0 \le L \le 2^{32}-1$). |

### Channel Types

| Channel Code | Identifier      |          Direction          | Payload Description                                               |
| :----------: | :-------------- | :-------------------------: | :---------------------------------------------------------------- |
|    `0x00`    | `PROCESS_EXIT`  | Client $\rightarrow$ Server | Terminal EOF frame signaling the completion of command execution. |
|    `0x01`    | `STDOUT`        | Client $\rightarrow$ Server | Standard output stream chunk.                                     |
|    `0x02`    | `STDERR`        | Client $\rightarrow$ Server | Standard error stream chunk.                                      |
|    `0x03`    | `STDIN`         | Server $\rightarrow$ Client | Standard input and execution payload bus.                         |
|    `0x04`    | `SIGNAL`        |       Bi-directional        | Out-of-band process signal (e.g. `SIGINT`, `SIGTERM`).            |
|    `0x05`    | `HEARTBEAT`     |       Bi-directional        | Keep-alive probe frame (payload length may be 0).                 |

## Client Bootstrap & Launcher Delivery

To establish a zero-disk client session, `py_socket` prepares the client bootstrap script through a 4-step pipeline:

1. **Template Interpolation**: Injects server host, port, and acknowledgment token into `py_socket_client.py`.
2. **Native AST Sanitization**: Strips comments, docstrings, type annotations, and development assertions using `declusor.lang.python.sanitize_source()` without external dependencies.
3. **Base64 Payload Encoding**: Encodes the sanitized source into a compact Base64 ASCII payload, eliminating quote escapes, multi-line formatting issues, and shell syntax clashes.
4. **Self-Contained Wrapper Template**: Delivers the launcher in a `LauncherDelivery` envelope configured with `PySocketRuntime.DEFAULT_WRAPPER_TEMPLATE`:
   ```bash
   python3 -c "import base64;exec(base64.b64decode('$DECLUSOR_SCRIPT'))"
   ```
   Executing this one-liner on the target decodes and starts the client agent entirely in memory.

## Session Lifecycle & State Machine

### Sequence Diagram

The sequence diagram illustrates the two-stage protocol lifecycle spanning initial handshake verification and multiplexed TLV command execution.

```mermaid
sequenceDiagram
    autonumber
    participant Server as Declusor Server
    participant Transport as TCP Transport
    participant Client as Python Client Agent

    Note over Server,Client: Stage 1: Handshake, Compatibility Negotiation & Helper Delivery
    Client->>Transport: Outbound TCP Connection Established
    Client->>Transport: STDOUT Frame [channel=0x01, len=M, payload=Runtime Metadata JSON]
    Transport->>Server: Read metadata frame & evaluate is_bytecode_compatible
    alt Bytecode Compatible (Matching Runtimes)
        Server->>Transport: STDOUT Frame [channel=0x01, len=N, payload=Marshaled Bytecode Helpers]
        Transport->>Client: Deliver helpers
        Client->>Client: marshal.loads(helpers) & exec in _SESSION_SCOPE
    else Bytecode Incompatible (Cross-Version Fallback)
        Server->>Transport: STDOUT Frame [channel=0x01, len=N, payload=UTF-8 Source Helpers]
        Transport->>Client: Deliver helpers
        Client->>Client: compile(helpers, "<helpers>", "exec") & exec in _SESSION_SCOPE
    end
    Client->>Transport: Raw Client ACK Token (32-byte SHA-256)
    Transport->>Server: Read exact 32 bytes & verify
    Note over Server,Client: Handshake Complete (State: CONNECTED)

    Note over Server,Client: Stage 2: Server-Driven Execution over STDIN & Streaming Loop
    Server->>Transport: STDIN Frame [channel=0x03, len=M, payload=composed_statement]
    Transport->>Client: Deliver statement on STDIN bus
    alt Python Evaluation (In-Memory)
        Client->>Client: Evaluate in _SESSION_SCOPE (e.g. execute_source, store_file)
    else Subprocess Execution (Real-Time Streaming)
        Client->>Client: subprocess.Popen (via execute_system_command or execute_binary)
        loop Real-Time Chunk Streaming
            Client->>Transport: STDOUT Frame [channel=0x01, len=4096, payload=chunk]
            Transport->>Server: Yield chunk
        end
        Client->>Client: proc.wait()
    end
    opt Buffered Output Generated
        Client->>Transport: STDOUT Frame [channel=0x01, len=K, payload=output]
        Transport->>Server: Yield output chunk
    end
    Client->>Transport: PROCESS_EXIT Frame [channel=0x00, len=0]
    Transport->>Server: Close command stream, yield completed
```

### Connection State Machine & Method Invariants

The connection state machine governs lifecycle transitions across `CREATED`, `INITIALIZING`, `CONNECTED`, and `CLOSED`, strictly enforcing I/O invariants.

```mermaid
stateDiagram-v2
    [*] --> CREATED: __init__()
    CREATED --> INITIALIZING: handshake() initiated
    INITIALIZING --> CONNECTED: 32-byte SHA-256 ACK verified
    INITIALIZING --> CLOSED: Handshake failed / error
    CONNECTED --> CLOSED: close() / socket disconnect
    CREATED --> CLOSED: close()
    CLOSED --> CLOSED: close() [Idempotent]

    note right of CREATED
        write() -> ConnectionError
        read() -> ConnectionError
        handshake() -> Permitted
    end note

    note right of INITIALIZING
        Internal handshake write/read -> Permitted
        handshake() -> ConnectionError
    end note

    note right of CONNECTED
        write() -> Permitted
        read() -> Permitted
        handshake() -> ConnectionError
    end note

    note right of CLOSED
        write() -> ConnectionClosed
        read() -> ConnectionClosed
        handshake() -> ConnectionError
        close() -> No-op
    end note
```

| Method        | `CREATED`         | `INITIALIZING`     | `CONNECTED`       | `CLOSED`           | Resulting State                      |
| :------------ | :---------------- | :----------------- | :---------------- | :----------------- | :----------------------------------- |
| `handshake()` | Allowed           | `ConnectionError`  | `ConnectionError` | `ConnectionError`  | `CONNECTED` (or `CLOSED` on failure) |
| `write(data)` | `ConnectionError` | Allowed (internal) | Allowed           | `ConnectionClosed` | Unchanged                            |
| `read()`      | `ConnectionError` | Allowed (internal) | Allowed           | `ConnectionClosed` | Unchanged                            |
| `close()`     | Allowed           | Allowed            | Allowed           | Allowed (No-op)    | `CLOSED`                             |

## Frame Encoding & Decoding Reference

### Python Reference (Server-Side)

```python
import struct
from declusor import config


# Frame transmission:
def send_command(transport, command_bytes: bytes) -> None:
    header = struct.pack(">BI", config.ChannelType.STDOUT, len(command_bytes))
    transport.write(header + command_bytes)


# Frame reception:
def read_stream(transport):
    while True:
        header = transport.read_exact(5)
        channel, length = struct.unpack(">BI", header)

        if channel == config.ChannelType.PROCESS_EXIT:
            if length > 0:
                transport.read_exact(length)
            return

        payload = transport.read_exact(length)
        if channel in (config.ChannelType.STDOUT, config.ChannelType.STDERR):
            yield payload
```

### Python Reference (Client-Side)

```python
import socket
import struct


def send_frame(sock: socket.socket, channel: int, data: bytes) -> None:
    sock.sendall(struct.pack(">BI", channel, len(data)) + data)


def read_frame(sock: socket.socket) -> bytes | None:
    header = read_exact(sock, 5)
    if header is None:
        return None
    channel, length = struct.unpack(">BI", header)
    return read_exact(sock, length)
```
