# Utility Package

The **util** package provides stateless helper functions consumed across every layer of the application.

> [!NOTE]
> Depends only on `config` (for exceptions and constants) — no circular dependencies.

## Modules

| Module           | Key Exports                                                                                                  | Responsibility                                                   |
| ---------------- | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------- |
| `concurrency.py` | `Task`, `TaskEvent`, `TaskHandler`, `TaskPool`                                                               | Thread-based cooperative concurrency for the interactive shell   |
| `encoding.py`    | `convert_bytes_to_hex`, `convert_to_base64`, `convert_base64_to_bytes`, `hash_*`, `quote`, `format_template` | Data encoding, hashing, shell quoting, and template formatting   |
| `network.py`     | `await_connection`                                                                                           | Context-manager socket listener with user-friendly error mapping |
| `parsing.py`     | `Parser`, `parse_command_arguments`                                                                          | Custom `argparse` subclass and type-aware argument parsing       |
| `security.py`    | `validate_file_extension`, `validate_file_relative`                                                          | Path-traversal and file-extension guards                         |
| `storage.py`     | `load_file`, `try_load_file`, `ensure_file_exists`, `ensure_directory_exists`                                | File loading and existence validation                            |

## Design Principles

1. **Statelessness** — all functions are pure or only depend on `config` constants.
2. **Single Purpose** — each function performs exactly one well-defined operation.
3. **Defensive Programming** — inputs are validated; errors raise `InvalidOperation` or `ConnectionFailure`.
4. **Type Safety** — all functions carry full type annotations.
