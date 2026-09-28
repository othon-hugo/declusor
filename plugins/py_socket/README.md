# Python Socket Plugin (`py_socket`)

The `py_socket` plugin provides a cross-platform reverse-shell client capable of executing payloads directly in-memory or delegating to the operating system shell. The agent is implemented in pure Python (standard library only), ensuring seamless execution across Linux, macOS, and Windows.

## Modules

| Module       | Responsibility                                                                  |
| ------------ | ------------------------------------------------------------------------------- |
| `connection` | Python socket connection transport, protocol profile, and asset file store      |
| `plugin`     | Entry-point plugin class (`IPluginExtension`), runtime orchestrator, and assets |

## Architecture & Execution Flow

The remote client discriminates between native Python code and shell commands using multi-line heuristic analysis (supporting shebangs, leading comments, docstrings, statements, and registered session functions).

```mermaid
flowchart TD
    START([Incoming Null-Terminated Payload]) --> STRIP[Strip Leading Comments & Docstrings]
    STRIP --> PARSE_AST{Python Check: Shebang, Session Scope, Keywords}

    PARSE_AST -->|Python Code| IN_MEMORY[In-Memory Execution]
    PARSE_AST -->|Shell Syntax / Command| SUBPROC[Subprocess Real-Time Streaming]

    subgraph In-Memory Pipeline
        IN_MEMORY --> REDIRECT[Redirect stdout/stderr to buffer]
        REDIRECT --> EXEC[exec payload in _SESSION_SCOPE]
        EXEC --> CATCH[Catch Exception AND SystemExit]
        CATCH --> RESTORE[Restore stdout/stderr]
        RESTORE --> SEND_INMEM[sock.sendall output]
    end

    subgraph Subprocess Streaming Pipeline
        SUBPROC --> SPAWN[subprocess.Popen shell=True stdout=PIPE stderr=STDOUT]
        SPAWN --> STREAM_LOOP{Read 4KB Chunk}
        STREAM_LOOP -->|Data| SEND_CHUNK[sock.sendall chunk] --> STREAM_LOOP
        STREAM_LOOP -->|EOF| WAIT[proc.wait]
    end

    SEND_INMEM --> SEND_ACK[sock.sendall ACKNOWLEDGE]
    WAIT --> SEND_ACK
    SEND_ACK --> DONE([Wait for Next Payload])
```

### Handshake & Command Protocol

```mermaid
sequenceDiagram
    autonumber
    participant Server as Declusor Server
    participant Sock as TCP Socket
    participant PyAgent as Python Agent Loop

    Server->>Sock: Connect TCP Socket
    Server->>Sock: Helper Libraries Bundle (file.py) + Null Delimiter
    PyAgent->>PyAgent: exec() helpers into _SESSION_SCOPE
    PyAgent->>Sock: Send Client ACK Sentinel
    Note over Server,PyAgent: Handshake Complete (State: CONNECTED)

    loop Command Dispatch Loop
        Server->>Sock: Null-Delimited Payload
        alt Python Payload (Shebang / Keywords / Session Funcs)
            PyAgent->>PyAgent: exec() in _SESSION_SCOPE with stdout capture
            PyAgent->>Sock: Send captured output + ACK
        else Shell Command / Binary
            PyAgent->>PyAgent: subprocess.Popen streaming stdout in real time
            PyAgent->>Sock: Stream chunks -> proc.wait() -> send ACK
        end
        Server-->>Server: Detect Client ACK, yield chunks to REPL
    end
```

## Design Principles

1. **Pure Python Standard Library** — Requires zero external dependencies, guaranteeing out-of-the-box compatibility on Linux, macOS, and Windows.
2. **Dual-Mode Execution** — Dynamically evaluates Python code in-memory within a persistent `_SESSION_SCOPE` or streams shell commands via subprocess pipes.
3. **Real-Time Subprocess Streaming** — Streams subprocess command output in 4KB chunks immediately without blocking execution or buffering complete outputs in memory.
4. **Agent Resilience & SystemExit Protection** — Wraps in-memory execution in traps catching both `Exception` and `SystemExit`, preventing client termination when scripts call `sys.exit()`.
5. **Contract Conformance** — Strictly adheres to `IPluginExtension`, `IPluginRuntime`, and `IConnection` interfaces.
