# Concurrency Invariants Specification

This document specifies the thread safety guarantees, worker pool lifecycles, task synchronization primitives, and state consistency rules enforced in Declusor using Lean BDD.

### CON-01: Cooperative Worker Shutdown and Timeout Reporting

Managed task pools signal cooperative cancellation on scope exit and join workers up to the configured timeout. Workers that do not stop before the timeout are recorded with `TimeoutError` and surfaced by the pool; Python threads cannot be forcibly terminated by the pool.

```gherkin
Scenario: Join cooperative workers when the pool exits
  Given a managed task pool with workers that respond to the shared stop event
  When the pool execution scope exits
  Then the pool signals cancellation and joins every worker before returning

Scenario: Report a worker that misses its join timeout
  Given a managed task pool with a worker that does not respond before the join timeout
  When the pool drains its tasks
  Then that task records a TimeoutError and the pool surfaces the failure
```

### CON-02: Interactive Shell Cross-Task Coordination

Interactive shell streaming must coordinate foreground input reading and background output streaming using non-blocking signaling, terminating both tasks when either side signals completion or disconnection.

```gherkin
Scenario: Coordinate interactive input and output streaming tasks
  Given an interactive shell session with concurrent input reading and output streaming
  When the remote output stream terminates due to client disconnection
  Then cancellation is signaled and both concurrent tasks terminate cleanly without deadlock
```

### CON-03: Interactive Shell Guaranteed Connection Timeout Restoration

The interactive shell command must record the connection's original timeout, set the timeout to blocking mode for interactive streaming, and unconditionally restore the original timeout upon completion.

```gherkin
Scenario: Restore original socket timeout upon shell completion
  Given a connection configured with an operational timeout T
  When interactive shell mode exits normally or terminates due to an error
  Then the connection timeout is unconditionally restored to T
```

### CON-04: Socket Transport Single-Reader / Single-Writer Separation

Transport connections must maintain strict structural separation between reading and writing routines; concurrent read calls or concurrent write calls on the same underlying unbuffered socket are disallowed.

```gherkin
Scenario: Maintain structural isolation between socket reader and writer tasks
  Given concurrent interactive shell operations over a stream transport
  When data is transmitted and received simultaneously
  Then reading and writing operate through independent, non-interfering task channels
```
