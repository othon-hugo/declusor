# Declusor Domain Invariants & Business-Rule Catalogs

This directory contains the authoritative specification of all domain invariants, protocol contracts, state-machine transitions, concurrency constraints, security barriers, and plugin business rules governing the Declusor framework.

## Catalog Index

| Document                                         | Category                     | Code  | Scope & Focus                                                                                                          |
| :----------------------------------------------- | :--------------------------- | :---- | :--------------------------------------------------------------------------------------------------------------------- |
| [**`domain.md`**](specs/domain.md)               | Domain Invariants            | `DOM` | Fail-fast validation checks raising centralized domain exceptions across CLI parsing, commands, and routing.           |
| [**`protocol.md`**](specs/protocol.md)           | Protocol & Contract          | `PRO` | Behavioral contracts and streaming guarantees of `ITransport`, `IView`, `IInputSource`, and transport framing.         |
| [**`lifecycle.md`**](specs/lifecycle.md)         | State-Machine & Lifecycle    | `STA` | Connection state transitions (`CREATED -> INITIALIZING -> CONNECTED -> CLOSED`), prompt loop signals, and teardown.    |
| [**`concurrency.md`**](specs/concurrency.md)     | Concurrency Invariants       | `CON` | Thread pool management (`TaskPool`), thread-safe signaling (`TaskEvent`), timeout restoration, and socket concurrency. |
| [**`security.md`**](specs/security.md)           | Security Invariants          | `SEC` | Path confinement, XOR obfuscation limits, cryptographic nonces, shell escaping, and null-byte defenses.                |
| [**`conformance.md`**](specs/conformance.md)     | Plugin Conformance           | `PLG` | Plugin metadata, routes, discovery precedence, asset validation, and native client handshake contracts.                |
| [**`cross-cutting.md`**](specs/cross-cutting.md) | Cross-Cutting Business Rules | `XCT` | CLI composition root wiring, factory signature introspection, deterministic exit codes, and dual-stream isolation.     |

## Schema & Governance

All catalog entries strictly adhere to the specification schema defined in [**`TEMPLATE.md`**](specs/TEMPLATE.md).

When introducing new domain entities, commands, protocol handlers, or plugins, new invariants must be cataloged here alongside their corresponding deterministic unit, integration, or conformance tests.
