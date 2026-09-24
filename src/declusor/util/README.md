# Utility Package

The **util** package provides stateless helper functions consumed across every layer of the application.

> [!NOTE]
> Depends only on `config` (for exceptions and constants) — no circular dependencies.

## Modules

| Module        | Responsibility                                                   |
| ------------- | ---------------------------------------------------------------- |
| `concurrency` | Thread-based cooperative concurrency for the interactive shell   |
| `encoding`    | Data encoding, hashing, shell quoting, and template formatting   |
| `network`     | Context-manager socket listener with user-friendly error mapping |
| `parsing`     | Custom `argparse` subclass and type-aware argument parsing       |
| `security`    | Path-traversal and file-extension guards                         |
| `storage`     | File loading and existence validation                            |

## Design Principles

1. **Statelessness** — all functions are pure or only depend on `config` constants.
2. **Single Purpose** — each function performs exactly one well-defined operation.
3. **Defensive Programming** — inputs are validated; errors raise `InvalidOperation` or `ConnectionFailure`.
4. **Type Safety** — all functions carry full type annotations.
