# Parent-Child Cancellation

## Central Question

How should cancellation propagate between a parent session and its child sessions without stopping independent work or leaving active operations behind?

## Scope

This research covers:

- parent-to-child cancellation;
- child-to-parent failure signaling;
- selective cancellation;
- cooperative cancellation state;
- deadlines and cancellation causes;
- teardown ordering and repeated cancellation.

It does not cover transport topology, resource ownership, environment state partitioning, authentication, or operating-system signal implementation.

## Hypothesis

Cancellation is predictable when every session has an explicit cancellation state, parent-to-child and child-to-parent propagation rules are different, operations can observe cancellation cooperatively, and teardown completes all dependent activity before a session becomes terminal.

The hypothesis fails if cancelling one child stops unrelated siblings, if cancellation is reported without stopping work, or if a parent becomes terminal while active children remain unmanaged.

## Cancellation Sources

A session may be cancelled by:

- explicit operator request;
- parent termination;
- child failure policy;
- deadline expiration;
- transport or runtime failure;
- process shutdown;
- resource limit exhaustion.

The source should be recorded because a user cancellation, timeout, and infrastructure failure may require different reporting and recovery.

## Cancellation State

A cancellation state should distinguish a request from completion:

```text
ACTIVE -> CANCELLATION_REQUESTED -> STOPPING -> CANCELLED
                                      |
                                      +-> FAILED
```

A cancellation request is not proof that the operation has stopped. The session should become terminal only after active work has observed the request, been interrupted, or been closed by an authoritative owner.

Repeated cancellation should be idempotent and should preserve the first meaningful cause unless the policy explicitly allows cause replacement.

## Parent-to-Child Propagation

Parent cancellation normally propagates to active children:

```text
cancel parent -> request cancellation for each child -> await child termination
```

The parent should stop admitting new children before propagating cancellation. Children created concurrently with the cancellation request must either be rejected or included deterministically.

A child may be allowed to drain gracefully, but the drain deadline must be explicit.

## Child-to-Parent Signaling

A child cancellation request should not automatically cancel the parent. A child may instead:

- report normal cancellation;
- report failure while the parent remains active;
- trigger parent cancellation when marked required;
- trigger sibling cancellation under a fail-fast policy.

The policy must distinguish a requested cancellation from an unexpected failure.

## Selective Cancellation

Cancelling one child should preserve unrelated siblings when they do not share an unrecoverable resource:

```text
cancel child A -> child A stops
                  child B continues
                  parent continues
```

Selective cancellation requires independent cancellation tokens, queues, operation records, and terminal transitions. A single shared event is insufficient when cancellation scopes differ.

## Cooperative Observation

Operations should check cancellation at safe boundaries:

- before starting work;
- between input chunks;
- while waiting for output;
- before committing a result;
- during cleanup.

Blocking operations need a way to wake when cancellation is requested. A task that cannot observe cancellation may prevent the parent from completing teardown.

Cancellation checks must not leave partially updated shared state.

## Deadlines

A deadline is a time limit associated with an operation or session. It should be propagated to children only when the policy requires a shared budget.

The system should define:

- whether child deadlines are absolute or relative;
- whether a child may request more time;
- what happens when the parent deadline expires;
- clock source and clock skew assumptions;
- behavior when cleanup exceeds the deadline.

A timeout should not be silently converted into a generic success or user cancellation.

## Teardown Ordering

A controlled parent teardown can follow this sequence:

```text
stop admitting children
    -> request child cancellation
    -> stop new operations
    -> interrupt or close blocking work
    -> await child terminal states
    -> release session state
    -> close parent
```

The exact order may vary, but no step should assume that a child stopped merely because a cancellation event was set.

## Minimal Experiment

1. Create one parent with two active children, `A` and `B`.
2. Cancel `A` and allow `B` to continue.
3. Make `A` fail and observe the parent policy.
4. Cancel the parent while `B` is processing input.
5. Attempt to create a child during parent cancellation.
6. Apply a deadline to the parent and a longer requested deadline to `B`.
7. Repeat cancellation and close operations.

Expected results:

- cancelling `A` does not stop `B` unless the policy says so;
- parent cancellation reaches every active child;
- child creation during parent teardown is rejected or deterministically included;
- blocking work eventually observes cancellation;
- terminal causes remain distinguishable;
- repeated cancellation and close are idempotent.

## Verification Strategy

Test:

1. child-only cancellation;
2. parent cancellation;
3. sibling failure;
4. fail-fast policy;
5. graceful drain;
6. deadline expiration;
7. cancellation during input wait;
8. cancellation during output delivery;
9. cancellation during cleanup;
10. repeated cancellation and close.

Record cancellation source, propagation path, session state, active operation count, terminal cause, and cleanup completion.

## Failure Modes and Limits

Common failures include:

- one shared cancellation flag stopping unrelated sessions;
- parent closing before children finish;
- child creation racing with parent cancellation;
- a cancellation request that never reaches a blocked operation;
- losing the original failure cause;
- treating cancellation as success without recording it;
- allowing cleanup to start new work;
- using relative timeouts that exceed the parent deadline.

Cancellation cannot guarantee immediate termination for code or external operations that do not provide an interruption boundary.

## Practical Conclusion

Cancellation should be modeled as scoped, observable state propagation rather than a single boolean event. Parent cancellation may cascade, child cancellation should normally remain local, and every terminal transition must account for active work and cleanup completion.

The central design rule is:

> Requesting cancellation changes what work may continue; only completed teardown proves that the work has stopped.
