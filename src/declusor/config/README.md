# Configuration Package

The **config** package sits at the base of the dependency hierarchy. It provides shared constants, enumerations, and exceptions consumed by every other package.

> [!NOTE]
> This package has **zero dependencies** on other application packages.

## Modules

| Module       | Responsibility                                                                               |
| ------------ | -------------------------------------------------------------------------------------------- |
| `enums`      | Enumerations for execution modes, connection states, operation codes, and transport channels |
| `exceptions` | Canonical domain exception hierarchy and custom warnings                                     |
| `settings`   | Configuration paths, runtime directories, and client configuration options                   |

## Exception Hierarchy

```
DeclusorException (Exception)
├── ConnectionError
│   ├── ConnectionClosed
│   ├── ConnectionTimeoutError
│   └── ConnectionHandshakeError
├── StorageError
│   └── StorageValidationError
├── PluginError
│   ├── PluginNotFoundError
│   ├── PluginValidationError
│   └── LauncherDeliveryError
├── CommandError
│   └── CommandValidationError
├── ControllerError
├── RouterError
│   └── DuplicateRouteError
├── PromptError
├── ParserError
└── InvalidOperation

DeclusorWarning (Warning)
```

## Design Principles

1. **Centralisation** — all settings and constants live here.
2. **Immutability** — values are class-level constants, not mutated at runtime.
3. **Type Safety** — `StrEnum` members and typed exceptions prevent invalid states.
4. **Semantic Exceptions** — each exception type conveys specific error context.

Route names are open-ended strings defined by route registrations, not a closed configuration enum. The plugin contract and `core.OFFICIAL_ROUTES` provide the types and reusable defaults for route declarations.
