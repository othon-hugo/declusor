# Main Package

The **main** package is the application entry point. It bootstraps all components, wires dependencies, and manages the service lifecycle.

## Modules

| Module         | Contents                                                                                                                                                                 |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `service.py`   | `DeclusorService` — top-level orchestrator that creates the profile, opens a connection, initialises the library handshake, registers routes, and starts the prompt loop |
| `exception.py` | `handle_unrecoverable_error` — catches fatal errors and prints user-friendly messages                                                                                    |

## Lifecycle

1. Parse CLI arguments (`host`, `port`).
2. Create `ShellSocketProfile` and display the client one-liner.
3. Listen for an incoming connection via `await_connection`.
4. Initialise the session (library upload + ACK handshake).
5. Wire controllers into the `Router`.
6. Start the `PromptCLI` run loop.
7. On exit (`ExitRequest` or `Ctrl-C`), clean up the connection context manager.

## Design Principles

1. **Single Entry Point** — `DeclusorService.run()` is the only public API.
2. **Dependency on Core** — main depends on core/connection implementations, never the reverse.
3. **Graceful Degradation** — fatal errors produce human-readable messages, not stack traces.
4. **Minimal Logic** — business logic lives in other packages; main handles only orchestration.
