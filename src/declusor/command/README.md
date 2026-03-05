# Command Package

The **command** package contains the executable command implementations that define discrete operations performed on remote targets. Each command encapsulates a specific action and its associated logic, adhering to the Command design pattern.

## Purpose

This package serves as the operational layer of the application, providing:

- **Action Encapsulation**: Each command represents a single, well-defined operation that can be executed on a remote session.
- **Session Interaction**: Commands are responsible for formatting and transmitting data to remote targets through the session abstraction.
- **Reusability**: Command objects are independent of the controllers that invoke them, enabling reuse across different contexts.
- **Interface Implementation**: All commands implement the `ICommand` interface from the domain layer.

## Design Principles

1. **Single Responsibility**: Each command performs exactly one operation.
2. **Interface Compliance**: All commands implement the `ICommand` interface, ensuring consistent execution patterns.
3. **Dependency on Abstractions**: Commands depend on `IConnection` and `IConsole` interfaces, not concrete implementations.
4. **Stateless Execution**: Commands receive all necessary state through their constructors and execution parameters.

## Expected Behavior

Commands within this package should:

- Accept configuration through constructor parameters
- Execute their operation via a synchronous `execute` method
- Interact with sessions solely through the `IConnection` interface
- Handle data encoding and formatting as required by the target protocol
- Remain agnostic to the origin of their invocation
