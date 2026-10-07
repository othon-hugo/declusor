# Session Close Order

## Central Question

What order of operations preserves correctness when a parent session, child sessions, runtimes, and transports must close while work or failures are still active?

## Scope

This research covers:

- close ordering for parent and child sessions;
- stopping admission of new work;
- draining or cancelling active operations;
- resource and runtime cleanup;
- simultaneous failures;
- idempotent close and primary failure reporting.

It does not cover resource ownership policy, runtime reset semantics, transport topology, authentication, or cancellation propagation in detail.

## Hypothesis

Session shutdown is reliable when new work is rejected before teardown starts, active work reaches a defined terminal state, child sessions close before their parent, resources close after dependent operations stop, and repeated close calls preserve the first meaningful outcome.

The hypothesis fails if cleanup closes a resource while it is still in use, if new work starts during teardown, or if concurrent failures produce inconsistent terminal results.

## Close Phases

A controlled close can use these phases:

```text
OPEN
  -> STOPPING_ADMISSION
  -> DRAINING_WORK
  -> CLOSING_CHILDREN
  -> CLOSING_RUNTIME
  -> CLOSING_TRANSPORT
  -> CLOSED
```

A forced failure may skip graceful draining, but it should still preserve the same dependency order where possible.

## Stop Admission First

The first close action should prevent new work from entering the session:

- reject new child creation;
- reject new operations;
- reject new resource acquisition;
- mark the session as closing;
- publish the closing state to observers.

Admission and close must be synchronized. Checking that a session is open and starting work later creates a race in which work can begin after teardown has started.

## Active Work

After admission stops, existing work must be handled according to policy:

- graceful drain until completion;
- cooperative cancellation;
- forced interruption;
- bounded wait followed by escalation.

The session must distinguish work that completed, work that was cancelled, and work that failed during closing. A timeout in the drain phase should not be reported as successful completion.

## Child Ordering

A parent should close active children before releasing resources required by those children:

```text
parent stops admission
    -> children stop admission
    -> children drain or cancel work
    -> children become terminal
    -> parent releases shared runtime state
    -> parent closes transport
```

A child may close independently while the parent remains active. Parent closure must still account for every child that is active or transitioning.

## Runtime and Resource Ordering

A runtime should remain available until operations using it have stopped. A transport should remain available until required terminal messages, diagnostics, or cleanup operations have completed or been explicitly abandoned.

The order should follow dependency:

```text
operations -> child state -> runtime state -> transport -> session record
```

Closing a lower-level dependency first can turn a normal teardown into an avoidable failure.

## Concurrent Failures

Multiple failures may occur during teardown:

- an operation fails while a child is closing;
- the transport closes while the runtime is resetting;
- a sibling reports failure while the parent is draining;
- cleanup itself raises an exception.

The system should define:

- which failure becomes the primary cause;
- which failures are attached as secondary causes;
- whether all cleanup steps still run;
- what observers receive;
- whether the final state is `CLOSED`, `FAILED`, or `CLOSED_WITH_ERRORS`.

The primary cause should not be overwritten by a later cleanup error without an explicit policy.

## Idempotency

Close can be called from several paths: normal completion, cancellation, timeout, exception handling, and parent teardown.

Repeated close should:

- not reopen the session;
- not start duplicate cleanup;
- not close a resource twice when that is unsafe;
- return or preserve the same terminal result;
- remain safe after partial cleanup.

Concurrent close calls should coordinate through one close operation or an equivalent state machine.

## Observer Visibility

Observers should see state transitions in a meaningful order:

```text
ACTIVE -> CLOSING -> CLOSED
```

A session should not announce `CLOSED` while child operations or required cleanup remain active. If forced close abandons work, that fact should be represented in the terminal result.

Diagnostics should remain available after closure long enough for consumers to retrieve them.

## Minimal Experiment

1. Create a parent with two active children and one shared runtime.
2. Start work in both children.
3. Request a graceful parent close.
4. Attempt to create new work during teardown.
5. Make one child fail while the other drains.
6. Close the transport before the drain completes.
7. Invoke close again from multiple concurrent callers.
8. Inspect final states, causes, cleanup calls, and retained diagnostics.

Expected results:

- new work is rejected after closing begins;
- children reach terminal states before dependent parent resources close;
- one child failure does not erase the other child's terminal result;
- transport failure is reported according to the documented policy;
- cleanup runs once or is safely idempotent;
- the primary failure cause remains stable;
- no session reports closed while required work is still active.

## Verification Strategy

Test:

1. normal graceful close;
2. close with active children;
3. child failure during parent close;
4. transport failure during drain;
5. runtime cleanup failure;
6. forced close after deadline;
7. concurrent close calls;
8. close after partial initialization;
9. close after prior failure;
10. observer reads during each phase.

Record state, active work, child states, resource state, primary cause, secondary causes, and cleanup count.

## Failure Modes and Limits

Common failures include:

- admitting work after teardown begins;
- closing the transport before child diagnostics are delivered;
- closing runtime state while an operation still references it;
- losing the first failure when cleanup raises another error;
- reporting success after forced abandonment;
- running cleanup multiple times without idempotency;
- allowing concurrent close calls to race through state transitions;
- deleting diagnostics before observers can retrieve them.

No close order can guarantee graceful completion when a dependency is already unavailable. The policy must define what is abandoned and how that fact is reported.

## Practical Conclusion

Closing a session is a dependency-ordered state transition, not a single `close()` call. Stop admission first, settle active work, close children before their dependencies, preserve failure causes, and expose a terminal result only after the selected cleanup policy has completed.

The central design rule is:

> Close dependents before dependencies, and make forced abandonment observable.
