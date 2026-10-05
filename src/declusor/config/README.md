# Configuration Package

The **config** package sits at the base of the dependency hierarchy. It provides shared constants, enumerations, and exceptions consumed by every other package.

> [!NOTE]
> This package has **zero dependencies** on other application packages.

## Modules

| Module       | Responsibility                                                                                                  |
| ------------ | --------------------------------------------------------------------------------------------------------------- |
| `enums`      | Enumerations for execution modes, connection states, operation codes, controller routes, and controller actions |
| `exceptions` | Canonical domain exception hierarchy and custom warnings                                                        |
| `settings`   | Configuration paths, runtime directories, and client configuration options                                      |

## Exception Hierarchy

```
DeclusorException (Exception)
├── ConnectionError
│   ├── ConnectionClosed
│   ├── ConnectionTimeoutError
│   └── ConnectionHandshakeError
├── StorageError
│   └── StorageValidationError (StorageError, InvalidOperation)
├── PluginError
│   ├── PluginNotFoundError
│   ├── PluginValidationError
│   └── LauncherDeliveryError
├── CommandError
│   └── CommandValidationError (CommandError, InvalidOperation)
├── ControllerError
├── RouterError
│   └── DuplicateRouteError (RouterError, ValueError)
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

`ControllerType` provides the canonical built-in route identifiers. Plugins use its members in `supported_controllers` to declare which plugin-specific commands their runtime supports; `help` and `exit` remain application-wide routes.
