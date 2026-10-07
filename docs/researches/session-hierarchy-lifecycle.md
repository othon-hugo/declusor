# Session Hierarchy Lifecycle

## Central Question

How should a parent session create, manage, and terminate child sessions without leaving ambiguous states or orphaned work?

## Scope

This research covers:

- parent and child session identity;
- creation and admission rules;
- lifecycle state transitions;
- parent termination;
- child completion and failure;
- prevention of orphaned sessions.

It does not cover resource ownership, data-state partitioning, transport topology, authentication, or detailed cancellation policy.

## Hypothesis

A session hierarchy is predictable when every child has one parent, every transition is explicit, parent and child terminal states are ordered, and the system defines what happens to children when their parent pauses, fails, or closes.

The hypothesis fails if a child can outlive its parent without an explicit policy, if a closed parent accepts new children, or if the same child transition can be applied inconsistently by concurrent callers.

## Session Identity

A child session should have an identity distinct from its parent:

```text
parent_id -> child_id -> operation_id
```

The parent relationship should be immutable after creation unless the system explicitly supports reparenting. Child identifiers should not be reused while records, buffers, or events from the previous child remain observable.

The hierarchy should expose enough identity to answer:

- which parent created the child;
- which children remain active;
- which operation created the child;
- why the child ended;
- whether the parent is still valid.

## Admission Rules

Child creation should be allowed only when the parent is in an admitting state, such as `CREATED`, `ACTIVE`, or `PAUSED` if the policy permits it.

The system should reject creation when the parent is:

- closing;
- closed;
- failed;
- disposed;
- unknown;
- outside its child-count or resource limits.

Admission should be atomic with registration so that concurrent creation attempts cannot exceed the configured limit.

## Lifecycle States

A minimal child lifecycle may be:

```text
CREATED -> STARTING -> ACTIVE -> CLOSING -> CLOSED
                         |
                         +-> FAILED
```

The parent may remain active while children start and finish independently. A parent should not become terminal merely because one child completes unless that is the explicit policy.

Every state transition should have a single owner or synchronization rule. Repeating a terminal transition should be harmless or produce a defined result.

## Parent and Child State

Parent and child states are related but not identical.

For example:

| Parent state | New child        | Existing child                         |
| :----------- | :--------------- | :------------------------------------- |
| `ACTIVE`     | May be admitted  | May continue                           |
| `PAUSED`     | Policy-dependent | May pause or continue                  |
| `CLOSING`    | Reject           | Begin termination                      |
| `CLOSED`     | Reject           | Must be terminal                       |
| `FAILED`     | Reject           | Fail or detach only by explicit policy |

The policy must be explicit. Inferring child behavior from a state name is insufficient.

## Parent Termination

When a parent terminates, the system must choose one of these policies for active children:

- cascade termination;
- graceful drain;
- detach and reparent;
- preserve as independent sessions;
- reject parent termination until children finish.

Cascade termination is usually the simplest policy, but it must still define ordering and error reporting. Detachment is more complex because it changes ownership and lifetime relationships.

## Child Completion

A child completing normally should remove itself from the parent's active-child set after its terminal result is recorded.

The parent should retain enough history to distinguish:

- a child that never started;
- a child that completed successfully;
- a child that failed;
- a child that was cancelled by the parent;
- a child that was lost with a shared resource.

Removing a child from an active set must not erase the result needed by observers.

## Failure Propagation

A child failure should affect the parent only according to a documented policy:

- record the failure and keep the parent active;
- fail the parent when a required child fails;
- cancel sibling children;
- retry the child;
- mark the parent degraded.

The reverse relationship also needs a rule. A parent failure may terminate all children, but the failure cause should remain distinguishable from an independent child failure.

## Orphan Prevention

An orphan is a child that remains active after its parent can no longer manage it.

Prevention requires:

- parent existence checks during creation;
- parent-liveness checks during child startup;
- a terminal transition for children during parent closure;
- cleanup after partial creation;
- recovery for process or transport failure;
- periodic reconciliation when state can be lost.

A child should not report itself as active merely because its creation task started.

## Minimal Experiment

1. Create a parent session.
2. Create two children concurrently.
3. Complete one child normally.
4. Fail the other child during startup.
5. Attempt to create a new child while the parent is active.
6. Close the parent while one child remains active.
7. Attempt to create another child after parent closure.
8. Repeat parent closure and child terminal transitions.

Expected results:

- each child has one stable parent and unique identity;
- the completed child is removed from the active set after its result is recorded;
- startup failure does not leave an active child record;
- parent closure applies the documented child policy;
- creation after parent closure is rejected;
- repeated terminal transitions are deterministic and idempotent.

## Verification Strategy

Test:

1. normal parent and child creation;
2. concurrent child admission at the configured limit;
3. child startup failure;
4. child normal completion;
5. child cancellation;
6. parent pause and resume;
7. parent graceful close;
8. parent forced failure;
9. child creation during closing;
10. repeated close and recovery after partial creation.

Record parent state, child state, active-child membership, terminal cause, and observer-visible results after every transition.

## Failure Modes and Limits

Common failures include:

- accepting children after the parent entered a terminal state;
- creating a child record before resource creation and never cleaning it up;
- removing a child before its result is observable;
- propagating every child failure to the parent unintentionally;
- losing child termination events during parent shutdown;
- reusing child identifiers while stale events remain;
- allowing a child to continue without a defined parent policy;
- treating a started task as a fully active session.

The hierarchy is only as reliable as its recovery behavior after process, transport, or state-store failure.

## Practical Conclusion

A parent-child session model requires explicit admission, identity, state transitions, terminal ordering, and failure propagation. Parent closure must define the fate of every active child, and child completion must preserve observable results while removing active ownership.

The central design rule is:

> No child session should outlive its parent unless detachment is an explicit, observable lifecycle transition.
