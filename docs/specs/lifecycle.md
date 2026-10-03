# State-Machine & Lifecycle Invariants Specification

This document specifies the lifecycle state machines, valid and rejected state transitions, idempotency guarantees, and resource teardown invariants across Declusor connections and sessions using Lean BDD.

### STA-01: Connection Forward Progression State Machine

Connection sessions strictly follow a unidirectional forward lifecycle progression: `CREATED` $\rightarrow$ `INITIALIZING` $\rightarrow$ `CONNECTED` $\rightarrow$ `CLOSED`; backward or arbitrary state jumps trigger connection errors to prevent operating on invalid sessions.

```gherkin
Scenario: Enforce strict forward connection state transitions
  Given a newly instantiated connection in CREATED state
  When the connection executes handshake and completes session teardown
  Then the lifecycle state transitions strictly through CREATED -> INITIALIZING -> CONNECTED -> CLOSED
```

### STA-02: Rejection of Handshake on Closed Connection

Initiating a handshake sequence on an already closed connection raises `ConnectionError` to prevent attempting network I/O or state re-entry on terminated transport sockets.

```gherkin
Scenario: Reject handshake on terminated connection
  Given a connection whose lifecycle state is CLOSED
  When a handshake operation is initiated
  Then the operation fails with ConnectionError("Cannot initialize a closed connection.")
```

### STA-03: Rejection of I/O on Closed Connection

Transmitting data via write operations or receiving data via read operations on a closed connection raises `ConnectionClosed` to halt controller execution cleanly when a peer has disconnected.

```gherkin
Scenario: Reject read and write operations on closed connection
  Given a connection whose lifecycle state is CLOSED
  When a write or read operation is attempted
  Then the operation fails with ConnectionClosed
```

### STA-04: Rejection of Command I/O Prior to Connected State

Application commands must not transmit payload bytes across a connection until the handshake sequence has completed successfully (`state == CONNECTED`); pre-handshake command writes raise `ConnectionError`.

```gherkin
Scenario: Reject command writes prior to completing handshake
  Given a connection in CREATED state that has not completed its handshake
  When an application command attempts to write data across the connection
  Then writing fails with ConnectionError
```

### STA-05: Idempotency of Connection Close

Closing a connection must be completely idempotent; subsequent invocations of close on an already closed connection must return cleanly without secondary errors or repeated shutdown routines.

```gherkin
Scenario: Guarantee idempotent connection teardown
  Given a connection that has already been closed
  When close is called repeatedly on the connection
  Then each invocation completes without error and the state remains CLOSED
```

### STA-06: Prompt Loop Structured Lifecycle Signals

Interactive controller execution must signal session lifecycle intent via structured signals (`CONTINUE` vs `TERMINATE`) rather than control-flow exceptions; `TERMINATE` cleanly exits the prompt loop with code 0.

```gherkin
Scenario: Process structured controller lifecycle signals
  Given an interactive prompt loop dispatching commands
  When a controller returns a TERMINATE lifecycle signal
  Then the prompt loop exits immediately with success status
```

### STA-07: Application Run Guaranteed Resource Teardown

The top-level application runner must guarantee that all acquired network listeners and active client connections are closed upon termination under all conditions (success, error, or user interrupt).

```gherkin
Scenario: Guarantee complete resource teardown during application termination
  Given an application session encountering an error or interrupt during execution
  When the session terminates
  Then both the active client connection and network listener are closed and the error propagates
```
