# Configuration Package

The **config** package sits at the base of the dependency hierarchy. It provides shared constants, enumerations, and exceptions consumed by every other package.

> [!NOTE]
> This package has **zero dependencies** on other application packages.

## Modules

| Module          | Contents                                                                          |
| --------------- | --------------------------------------------------------------------------------- |
| `settings.py`   | `Settings` (project name/description) and `BasePath` (directory constants)        |
| `enums.py`      | `ClientFile` (client script filenames) and `OperationCode` (file operation codes) |
| `exceptions.py` | Full exception hierarchy rooted at `DeclusorException`                            |

## Exception Hierarchy

```
DeclusorException
├── InvalidOperation
├── ConnectionFailure
├── ParserError
├── RouterError
├── PromptError
├── ControllerError
└── ExitRequest

DeclusorWarning (Warning)
```

## Design Principles

1. **Centralisation** — all settings and constants live here.
2. **Immutability** — values are class-level constants, not mutated at runtime.
3. **Type Safety** — `StrEnum` members and typed exceptions prevent invalid states.
4. **Semantic Exceptions** — each exception type conveys specific error context.
