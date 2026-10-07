# Technical Research Catalog

This directory contains atomic technical researches that record reusable engineering knowledge about execution, representation, framing, transport, security, performance, compatibility, and testing.

Researches are investigative documents. They explain how a mechanism works, what evidence supports the conclusion, where the mechanism fails, and which practical decision follows. They are not authoritative specifications or implementation changelogs.

## Catalog Index

| Document                                                                           | Category       | Scope and Focus                                                                             |
| :--------------------------------------------------------------------------------- | :------------- | :------------------------------------------------------------------------------------------ |
| [`bash-stdin-execution.md`](bash-stdin-execution.md)                               | Execution      | Executing Bash source from standard input without requiring a script file.                  |
| [`bash-interpreter-selection.md`](bash-interpreter-selection.md)                   | Compatibility  | Differences between Bash and generic `sh` interpreters.                                     |
| [`bash-runtime-environment.md`](bash-runtime-environment.md)                       | Execution      | Working directory, environment, identity, permissions, commands, locale, and shell options. |
| [`bash-stdin-transport-boundary.md`](bash-stdin-transport-boundary.md)             | Transport      | Separation between source bytes, encoding, transport, and interpretation.                   |
| [`python-in-memory-execution.md`](python-in-memory-execution.md)                   | Execution      | Compilation, execution namespaces, output handling, and process resources.                  |
| [`python-ast-source-sanitization.md`](python-ast-source-sanitization.md)           | Representation | AST-based removal of selected source constructs and semantic limits.                        |
| [`python-token-stream-filtering.md`](python-token-stream-filtering.md)             | Representation | Lexical filtering with token streams and its syntactic limitations.                         |
| [`python-compiler-optimization-levels.md`](python-compiler-optimization-levels.md) | Representation | Observable behavior of compiler optimization levels.                                        |
| [`python-marshal-code-objects.md`](python-marshal-code-objects.md)                 | Compatibility  | Serialization of code objects and interpreter compatibility boundaries.                     |
| [`python-payload-size-benchmark.md`](python-payload-size-benchmark.md)             | Performance    | Measuring source, serialized, encoded, and framed payload sizes.                            |
| [`framing-modes.md`](framing-modes.md)                                             | Framing        | Delimiter, length-prefixed, fixed-size, and self-describing framing.                        |
| [`shell-envelope-framing.md`](shell-envelope-framing.md)                           | Framing        | Nonce-delimited envelopes, fragmented markers, and logical EOF.                             |
| [`tlv-frame-reading.md`](tlv-frame-reading.md)                                     | Framing        | Exact TLV header/body reads, limits, channels, and truncation.                              |
| [`stream-obfuscation.md`](stream-obfuscation.md)                                   | Representation | Stateful reversible transformations and chunk synchronization.                              |
| [`stream-compression.md`](stream-compression.md)                                   | Representation | Compression placement, state, expansion limits, and measurement.                            |
| [`message-authentication.md`](message-authentication.md)                           | Security       | Message authenticity, integrity, tags, context, and freshness.                              |
| [`in-memory-is-not-sandbox.md`](in-memory-is-not-sandbox.md)                       | Security       | Why file-free or in-memory execution does not provide isolation.                            |
| [`transport-layer-composition.md`](transport-layer-composition.md)                 | Transport      | Layer delegation, ordering, lifecycle, and failure propagation.                             |
| [`interactive-shell-cancellation.md`](interactive-shell-cancellation.md)           | Lifecycle      | Cancellation, timeouts, disconnects, and cleanup ordering.                                  |
| [`parallel-session-isolation.md`](parallel-session-isolation.md)                   | Concurrency    | Concurrent session routing, independent state, backpressure, and failure isolation.         |
| [`session-hierarchy-lifecycle.md`](session-hierarchy-lifecycle.md)                 | Lifecycle      | Parent-child session states, admission, termination, and orphan prevention.                 |
| [`session-resource-ownership.md`](session-resource-ownership.md)                   | Lifecycle      | Resource ownership, borrowing, transfer, leases, and idempotent cleanup.                    |
| [`environment-state-partitioning.md`](environment-state-partitioning.md)           | Concurrency    | Shared, snapshot, and isolated state across concurrent sessions.                            |
| [`subsession-transport-topology.md`](subsession-transport-topology.md)             | Concurrency    | Dedicated connections, multiplexed channels, routing, backpressure, and failure domains.    |
| [`parent-child-cancellation.md`](parent-child-cancellation.md)                     | Lifecycle      | Scoped cancellation, deadlines, propagation, and parent-child teardown.                     |
| [`subsession-concurrency-policy.md`](subsession-concurrency-policy.md)             | Concurrency    | Parallelism scopes, serialization, admission limits, fairness, and backpressure.            |
| [`runtime-scope-and-reset.md`](runtime-scope-and-reset.md)                         | Lifecycle      | Runtime sharing, cloning, creation, pooling, reset, and failure states.                     |
| [`session-close-order.md`](session-close-order.md)                                 | Lifecycle      | Teardown ordering, child closure, failure causes, and idempotent shutdown.                  |
| [`sleep-agent.md`](sleep-agent.md)                                                 | Lifecycle      | State preservation, jitter dispersion, cold hibernation, memory masking, and retry limits.  |
| [`plugin-discovery-precedence.md`](plugin-discovery-precedence.md)                 | Extensibility  | Discovery sources, duplicate names, precedence, and origin reporting.                       |
| [`plugin-lifecycle-contract.md`](plugin-lifecycle-contract.md)                     | Extensibility  | Configuration, validation, runtime construction, and connection lifecycle.                  |
| [`operation-code-dispatch.md`](operation-code-dispatch.md)                         | Extensibility  | Separating abstract operations from runtime-specific rendering.                             |
| [`plugin-asset-resolution.md`](plugin-asset-resolution.md)                         | Security       | Asset roots, canonical paths, traversal, and symlink policy.                                |
| [`plugin-conformance-testing.md`](plugin-conformance-testing.md)                   | Testing        | Contract-oriented tests, typed doubles, and reusable conformance suites.                    |

## Research Governance

Every research should follow the structure defined in [`TEMPLATE.md`](TEMPLATE.md).

Before adding a document:

1. Confirm that it answers a question not already covered by another research.
2. Keep the topic narrow enough to validate with a focused experiment.
3. State explicit scope and non-scope.
4. Separate observed facts from assumptions.
5. Document failure modes and limits.
6. Avoid claims stronger than the available evidence.
7. Keep examples independent of private paths, names, and credentials.

## Research Versus Specification

Use a research when the goal is to understand a mechanism, compare alternatives, record an experiment, or preserve a reusable lesson.

Use a specification when the goal is to define an authoritative invariant, required behavior, error contract, or acceptance criterion.

A research may inform a specification, but it does not replace one.

## Quality Checklist

Each document should contain:

- [ ] One central technical question;
- [ ] A defined scope;
- [ ] A falsifiable hypothesis or explicit investigation goal;
- [ ] A reproducible experiment or observation;
- [ ] Failure modes and limitations;
- [ ] A practical conclusion;
- [ ] No unrelated topic disguised as a subsection.
