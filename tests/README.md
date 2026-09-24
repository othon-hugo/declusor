# Test Suite Architecture

Declusor maintains an automated test suite organized by architectural layer and test scope.

## 1. Directory Layout

```text
tests/
├── unit/
│   ├── command/         # Command DTO validation and command operation lifecycles
│   ├── config/          # Settings, BasePath, DataPaths, enums, and centralized exceptions
│   ├── contract/        # Abstract contracts, SessionContext coordinator, and interfaces
│   ├── controller/      # Controller handlers and parameter extraction
│   ├── core/            # Router, DeclusorParser, and PluginManager discovery
│   ├── main/            # Composition root (Application) and CLI entrypoint (main)
│   ├── plugins/         # Autonomous client plugins (shell_socket, py_socket)
│   ├── presentation/    # Console I/O, error formatting, and PromptCLI loop
│   └── util/            # Primitives: encoding, security, storage, network, concurrency, parsing
├── integration/
│   └── test_plugin_discovery_e2e.py  # End-to-end multi-tier plugin discovery
└── e2e/                 # End-to-end live session scenarios
```

## 2. Test Principles and Conventions

1. **Isolation & Invariants**: Unit tests mock boundary I/O (sockets, terminal I/O, filesystem where appropriate) using `unittest.mock` and `tmp_path`.
2. **Defensive Testing**: Invariant violations (e.g. empty commands, directory traversal, unsupported types) must explicitly verify the raised domain exceptions (`config.InvalidOperation`, `config.ParserError`, `config.RouterError`, etc.).
3. **No Cross-Layer Contamination**: Test helpers and imports follow the same strict dependency order as source packages.

## 3. Running the Tests

Run the complete test suite:
```bash
pytest tests -v
```

Run tests for a specific layer:
```bash
pytest tests/unit/config/ -v
pytest tests/unit/util/ -v
pytest tests/unit/plugins/ -v
```

Run integration tests:
```bash
pytest tests/integration/ -v
```
