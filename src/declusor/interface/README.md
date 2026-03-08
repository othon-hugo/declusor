# Interface Package (Domain Layer)

The **interface** package defines the abstract contracts that establish the boundaries between system components. This is the **domain layer** — pure abstractions with no implementation logic.

> [!NOTE]
> This package has **zero dependencies** on other application packages.

## Modules

| Module          | Interface     | Purpose                                                                       |
| --------------- | ------------- | ----------------------------------------------------------------------------- |
| `command.py`    | `ICommand`    | Contract for executable command objects                                       |
| `connection.py` | `IConnection` | Contract for session I/O (read/write/initialize) with context-manager support |
| `console.py`    | `IConsole`    | Contract for console I/O (messages, binary data, errors, warnings)            |
| `parser.py`     | `IParser`     | Contract for argument parsing                                                 |
| `profile.py`    | `IProfile`    | Contract for immutable connection configuration (host, port, client script)   |
| `prompt.py`     | `IPrompt`     | Contract for the interactive command loop                                     |
| `router.py`     | `IRouter`     | Contract for route registration, lookup, and documentation                    |

## Design Principles

1. **Pure Abstractions** — interfaces contain only `@abstractmethod` signatures and docstrings.
2. **Single Responsibility** — each interface defines exactly one concern.
3. **Minimal Surface** — only methods required by consumers are exposed.
4. **Liskov Substitution** — any implementation must be drop-in replaceable.

## Usage

- Concrete implementations reside in `core` (console, router, parser, prompt) and `connection` (session I/O).
- Type hints throughout the codebase reference interfaces, not concrete classes.
- Controllers and commands depend exclusively on interface types.
