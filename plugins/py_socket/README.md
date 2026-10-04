# Python Socket Plugin (`py_socket`)

The `py_socket` plugin provides a cross-platform reverse-shell client capable of executing payloads directly in-memory or delegating to the operating system shell. The agent is implemented in pure Python (standard library only), ensuring seamless execution across Linux, macOS, and Windows.

## Modules

| Module       | Responsibility                                                                                                        |
| ------------ | --------------------------------------------------------------------------------------------------------------------- |
| `connection` | Python socket connection transport (`PySocketConnection`) and protocol profile (`PySocketProfile`)                    |
| `plugin`     | Entry-point plugin (`PySocketPlugin`), runtime adapter (`PySocketRuntime`), and asset processor (`PySocketProcessor`) |

## Architecture & Execution Flow

The remote client discriminates between native Python code and shell commands using multi-line heuristic analysis (supporting shebangs, leading comments, docstrings, statements, and registered session functions).

```mermaid
flowchart TD
    START([Incoming TLV Command Frame]) --> STRIP[Strip Leading Comments & Docstrings]
    STRIP --> PARSE_AST{Python Check: Shebang, Session Scope, Keywords}

    PARSE_AST -->|Python Code| IN_MEMORY[In-Memory Execution]
    PARSE_AST -->|Shell Syntax / Command| SUBPROC[Subprocess Real-Time Streaming]

    subgraph In-Memory Pipeline
        IN_MEMORY --> REDIRECT[Redirect stdout/stderr to buffer]
        REDIRECT --> EXEC[exec payload in _SESSION_SCOPE]
        EXEC --> CATCH[Catch Exception AND SystemExit]
        CATCH --> RESTORE[Restore stdout/stderr]
        RESTORE --> SEND_INMEM[Send STDOUT Frame 0x01]
    end

    subgraph Subprocess Streaming Pipeline
        SUBPROC --> SPAWN[subprocess.Popen shell=True stdout=PIPE stderr=STDOUT]
        SPAWN --> STREAM_LOOP{Read 4KB Chunk}
        STREAM_LOOP -->|Data| SEND_CHUNK[Send STDOUT Frame 0x01] --> STREAM_LOOP
        STREAM_LOOP -->|EOF| WAIT[proc.wait]
    end

    SEND_INMEM --> SEND_EXIT[Send PROCESS_EXIT Frame 0x00 with exit code]
    WAIT --> SEND_EXIT
    SEND_EXIT --> DONE([Wait for Next Frame])
```

### Handshake & Command Protocol

For wire format specifications and frame headers, see [PROTOCOL.md](PROTOCOL.md).

```mermaid
sequenceDiagram
    autonumber
    participant Server as Declusor Server
    participant Sock as TCP Socket
    participant PyAgent as Python Agent Loop

    Server->>Sock: Connect TCP Socket
    PyAgent->>Sock: Client Runtime Metadata Frame (version, magic, platform)
    Server->>Server: Evaluate is_bytecode_compatible
    alt Bytecode Compatible
        Server->>Sock: Marshaled Bytecode Helpers Frame (channel=0x01)
        PyAgent->>PyAgent: marshal.loads() & exec in _SESSION_SCOPE
    else Bytecode Incompatible
        Server->>Sock: UTF-8 Source Helpers Frame (channel=0x01)
        PyAgent->>PyAgent: compile() & exec in _SESSION_SCOPE
    end
    PyAgent->>Sock: Send 32-Byte Client ACK Token
    Note over Server,PyAgent: Handshake Complete (State: CONNECTED)

    loop Command Dispatch Loop
        Server->>Sock: TLV Frame (channel=0x01, length=N, command)
        alt Python Payload (Shebang / Keywords / Session Funcs)
            PyAgent->>PyAgent: exec() in _SESSION_SCOPE with stdout capture
            PyAgent->>Sock: Send STDOUT Frame (0x01) + PROCESS_EXIT Frame (0x00)
        else Shell Command / Binary
            PyAgent->>PyAgent: subprocess.Popen streaming stdout in real time
            PyAgent->>Sock: Stream chunks (0x01) -> proc.wait() -> send PROCESS_EXIT Frame (0x00)
        end
        Server-->>Server: Yield chunks in real-time until EOF frame
    end
```

## Design Principles

1. **Pure Python Standard Library** — Requires zero external dependencies, guaranteeing out-of-the-box compatibility on Linux, macOS, and Windows.
2. **Dual-Mode & In-Memory Execution** — Dynamically negotiates bytecode compatibility during handshake, executing precompiled marshaled code objects or compiled Python source directly in-memory within a persistent `_SESSION_SCOPE` without touching disk, or streaming shell commands via subprocess pipes.
3. **Real-Time Subprocess Streaming** — Streams subprocess command output in 4KB chunks immediately without blocking execution or buffering complete outputs in memory.
4. **Agent Resilience & SystemExit Protection** — Wraps in-memory execution in traps catching both `Exception` and `SystemExit`, preventing client termination when scripts call `sys.exit()`.
5. **Contract Conformance** — Strictly adheres to `IPluginExtension`, `IPluginRuntime`, and `IConnection` interfaces.
6. **Zero-Disk Launcher Delivery** — Sanitizes the bootstrap client script using native AST pruning to eliminate comments, docstrings, annotations, and asserts, Base64-encodes the payload, and packages it into an immediate, copy-pasteable execution wrapper (`PySocketRuntime.DEFAULT_WRAPPER_TEMPLATE`).

