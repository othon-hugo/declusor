# Domain Invariant & Business Rule Specification Template

This document defines the standard specification schema for documenting domain invariants, protocol contracts, state-machine transitions, concurrency constraints, and security barriers in Declusor using a Lean BDD approach.

## Purpose

Specifications represent authoritative domain truths and business rules that define what the system must guarantee. In accordance with specification-first software engineering, these specifications are **implementation-agnostic**: they describe system behavior, domain boundaries, invariants, and error contracts prior to implementation.

They serve as:

1. **The Contract of Record**: An unambiguous description of required behavior independent of programming language, internal file paths, or private data structures.
2. **Defensive Testing Blueprint**: Executable Gherkin scenarios ready for test-driven development (TDD) and verification.
3. **Architectural Purity**: Clean boundaries defining what the domain model, protocol framing, and security barriers must enforce.

## Specification Categories

All specifications are cataloged under `docs/specs/<category>.md` across 7 structural categories:

| Category          | File                                   | Description                                                                          |
| :---------------- | :------------------------------------- | :----------------------------------------------------------------------------------- |
| **Domain**        | [`domain.md`](domain.md)               | Business validation rules, input constraints, and command invariants.                |
| **Protocol**      | [`protocol.md`](protocol.md)           | Behavioral stream contracts, message framing, and channel demultiplexing.            |
| **Lifecycle**     | [`lifecycle.md`](lifecycle.md)         | State-machine transitions, lifecycle progression, and teardown invariants.           |
| **Concurrency**   | [`concurrency.md`](concurrency.md)     | Thread pools, task synchronization, timeout guarantees, and socket safety.           |
| **Security**      | [`security.md`](security.md)           | Path confinement barriers, cipher symmetry, cryptographic entropy, and sanitization. |
| **Conformance**   | [`conformance.md`](conformance.md)     | Universal plugin contracts and client agent handshake specifications.                |
| **Cross-Cutting** | [`cross-cutting.md`](cross-cutting.md) | Application composition, factory dependency injection, and process exit contracts.   |

## Standard Specification Template (Lean BDD)

When authoring or updating entries in `docs/specs/<category>.md`, adhere strictly to the following Lean BDD markdown template:

````markdown
### `<CATEGORY_CODE>-<ID>`: `<Invariant Title>`

<Definitive statement of the invariant, the domain error emitted on breach, and the operational risk it mitigates.>

```gherkin
Scenario: <Descriptive scenario title>
  Given <preconditions or input state>
  When <action or boundary trigger>
  Then <expected behavior or domain error>
```
````

## Guidelines

1. **Identifier (`<CATEGORY_CODE>-<ID>`)**:
   - `DOM`: Domain Invariants
   - `PRO`: Protocol / Contract Invariants
   - `STA`: State-Machine / Lifecycle Invariants
   - `CON`: Concurrency Invariants
   - `SEC`: Security Invariants
   - `PLG`: Plugin Conformance Invariants
   - `XCT`: Cross-Cutting Business Rules
2. **Summary Statement**: A single crisp sentence or short paragraph uniting the rule, the domain error emitted if violated, and the operational blast radius prevented.
3. **Gherkin Scenario**: A concrete, falsifiable `Scenario:` with `Given`, `When`, and `Then` steps describing the exact behavioral acceptance criteria without leaking implementation file paths or private variable names.
