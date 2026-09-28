# Shell Socket Plugin (`shell_socket`)

The `shell_socket` plugin provides a lightweight, zero-dependency reverse-shell client using Linux's native `/dev/tcp` virtual file descriptor interface. It establishes an interactive bidirectional connection directly through Bash, requiring no external tools (such as `nc`, `socat`, or Python) on the target host.

## Modules

| Module       | Responsibility                                                                  |
| ------------ | ------------------------------------------------------------------------------- |
| `connection` | Reverse-shell connection transport, protocol profile, and asset file store      |
| `plugin`     | Entry-point plugin class (`IPluginExtension`), runtime orchestrator, and assets |

## Architecture & Protocol Flow

The client agent operates as a self-contained Bash loop utilizing file descriptor 3 mapped to `/dev/tcp`. Handshake negotiation and command execution follow a deterministic request-response cycle demarcated by acknowledgment tokens.

```mermaid
sequenceDiagram
    autonumber
    participant Server as Declusor Server
    participant FD3 as Remote /dev/tcp FD 3
    participant Bash as Client Execution Loop

    Server->>FD3: Connect TCP Socket
    Server->>FD3: Helper Libraries Bundle (util.sh, file.sh) + Server ACK
    Bash->>Bash: eval helpers in-memory (no disk write)
    Bash->>FD3: Send Client ACK Sentinel
    Note over Server,Bash: Handshake Complete (State: CONNECTED)

    loop Command Dispatch Loop
        Server->>FD3: Null-Delimited Payload + Server ACK
        Bash->>Bash: Check payload (eval in-memory vs disk-executable)
        alt In-Memory Shell Command / Script
            Bash->>FD3: eval "$data" >&3 2>&3
        else Native Binary Execution
            Bash->>Bash: Stage to writable exec path (/dev/shm -> /tmp -> /var/tmp)
            Bash->>FD3: Execute & stream output to >&3 2>&3
            Bash->>Bash: Unlink binary
        end
        Bash->>FD3: printf '%b' "$DECLUSOR_ACKNOWLEDGE" >&3
        Server-->>Server: Detect Client ACK, yield chunks to REPL
    end
```

## Design Principles

1. **Zero External Dependencies** — Relies entirely on Python standard library on the host and Linux Bash `/dev/tcp` virtual files on the remote target.
2. **In-Memory Script Execution** — Evaluates shell helper libraries and scripts directly in-memory via subshells, bypassing disk forensics and `noexec` partition restrictions.
3. **Contract Conformance** — Strictly implements `IPluginExtension`, `IPluginRuntime`, and `IConnection` contracts.
4. **Deterministic Framing** — Demarcates commands with null delimiters and tracks response completion via SHA-256 segmented ACK stream markers.
5. **Idempotent Lifecycle** — Guarantees safe multiple `close()` calls and deterministic lifecycle state transitions (`CREATED` -> `INITIALIZING` -> `CONNECTED` -> `CLOSED`).
