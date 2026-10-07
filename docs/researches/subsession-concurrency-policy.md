# Subsession Concurrency Policy

## Central Question

Which operations may run concurrently within and across subsessions, and where must execution be serialized to preserve correctness?

## Scope

This research covers:

- concurrency scopes;
- serialization and parallel execution;
- per-session and global limits;
- scheduling and fairness;
- backpressure;
- ordering and shared-state hazards.

It does not cover cancellation propagation, resource ownership, transport topology, environment partitioning, authentication, or implementation-specific thread pools.

## Hypothesis

Concurrency is safe when each operation declares its required scope, mutable state has an explicit serialization rule, parallel work has bounded admission, and scheduling prevents one subsession from monopolizing shared capacity.

The hypothesis fails if operations that share mutable state run concurrently without coordination, if limits are checked non-atomically, or if one subsession can consume all scheduler or queue capacity.

## Concurrency Scopes

An operation may require one of several scopes:

| Scope          | Meaning                                                     |
| :------------- | :---------------------------------------------------------- |
| Operation      | Only this operation's internal work is isolated.            |
| Subsession     | Operations in one subsession are serialized or coordinated. |
| Parent session | Sibling subsessions share a concurrency limit or lock.      |
| Transport      | All operations using one connection are serialized.         |
| Global         | The operation competes with every active session.           |

The narrowest safe scope should be selected. A global lock should not be used when a subsession-local lock is sufficient.

## Serial and Parallel Operations

Operations should be classified by their state and side effects:

- read-only operations may run concurrently when their inputs are stable;
- independent writes may run concurrently when their destinations do not overlap;
- mutations to shared state require serialization or a transactional policy;
- operations using one ordered stream may require a single writer;
- operations whose results depend on previous operations require ordering.

Concurrency should be a declared contract rather than an accidental property of the scheduler.

## Admission Control

Admission must reserve capacity atomically:

```text
check limit -> reserve slot -> start operation
```

Checking first and reserving later permits concurrent callers to exceed the limit.

Limits may apply to:

- active operations per subsession;
- active subsessions per parent;
- concurrent writers per transport;
- total queued bytes;
- total CPU or memory budget.

A rejected operation should be distinguishable from an operation that started and later failed.

## Scheduling and Fairness

A scheduler should define how ready work is selected:

- FIFO;
- round-robin by subsession;
- weighted priority;
- deadline-aware;
- resource-aware.

A continuously producing subsession must not starve other subsessions merely because it remains ready. Fairness may be relaxed for explicit priority classes, but the policy should be observable and bounded.

## Backpressure

Backpressure controls work when consumers or shared resources cannot keep up.

The policy should define whether a slow subsession causes the producer to:

- block;
- buffer up to a limit;
- drop data;
- reject new operations;
- fail the subsession;
- reduce its scheduling priority.

Backpressure should be applied at the smallest safe scope. A full queue for one subsession should not silently block unrelated subsessions unless they share a required ordered resource.

## Ordering

Parallel execution does not imply ordered results. The contract should specify whether ordering is required for:

- operations within one subsession;
- messages within one operation;
- responses across sibling subsessions;
- writes on one transport;
- state mutations.

When results may complete out of order, each result needs explicit correlation with its operation and subsession.

## Shared Mutable State

Parallel operations must not mutate shared state without one of:

- serialization;
- a lock with a defined scope;
- transactional isolation;
- immutable data;
- conflict detection and resolution.

A scheduler can prevent simultaneous execution but cannot guarantee correctness if a mutation occurs outside the scheduler's control.

## Minimal Experiment

1. Create two subsessions, `A` and `B`.
2. Run independent slow operations in both and measure overlap.
3. Run two conflicting mutations in one subsession.
4. Exceed the per-subsession and global operation limits concurrently.
5. Make `A` continuously produce output while `B` submits bounded work.
6. Fill `A`'s queue and observe `B`.
7. Complete operations out of order and verify response correlation.

Expected results:

- independent subsessions overlap within the configured limit;
- conflicting operations use the documented serialization rule;
- concurrent admission never exceeds limits;
- `B` receives scheduling capacity despite `A` being continuously ready;
- `A`'s backpressure affects only the documented scope;
- out-of-order completion does not misroute results.

## Verification Strategy

Test:

1. independent parallel operations;
2. conflicting operations in one subsession;
3. conflicting operations across siblings;
4. per-subsession limit;
5. parent or global limit;
6. fairness under sustained load;
7. slow consumer backpressure;
8. writer serialization;
9. out-of-order completion;
10. admission races.

Record operation scope, admission decision, scheduler order, queue size, start time, completion time, and result correlation.

## Failure Modes and Limits

Common failures include:

- using a global lock for all operations;
- allowing concurrent mutation of shared state;
- checking limits without atomic reservation;
- starvation caused by an always-ready producer;
- unbounded per-session queues;
- serializing unrelated sessions behind one slow consumer;
- relying on completion order for response routing;
- assuming task parallelism implies transport parallelism.

Parallelism is limited by shared state, ordered transports, CPU, memory, and external resources. Increasing concurrency does not necessarily increase useful throughput.

## Practical Conclusion

A concurrency policy should state which work may overlap, which state requires serialization, how capacity is reserved, how fairness is maintained, and how backpressure is contained. Subsessions can execute independently only when their data paths and mutable state support that independence.

The central design rule is:

> Concurrency is a contract about scope, ordering, capacity, and fairness, not merely the number of tasks started.
