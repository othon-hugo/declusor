# Interactive Shell Cancellation

## Central Question

How can an interactive shell stop input, output, and remote execution together when the operator, peer, or transport terminates?

## Scope

This research covers cancellation sources, cooperative shutdown, timeouts, EOF, interrupts, and cleanup ordering.

It does not cover shell framing, transport obfuscation, command rendering, or operating-system signal design in depth.

## Cancellation Sources

An interactive session may stop because of:

- operator interrupt;
- operator EOF;
- remote disconnect;
- transport error;
- command completion;
- timeout;
- explicit session close.

These causes should converge on a defined cancellation path while preserving their diagnostic origin.

## Shared Cancellation State

Concurrent input and output tasks need a shared cancellation signal:

```python
stop_requested = Event()
```

A task that observes a terminal condition should signal cancellation rather than waiting for another task to discover the same condition.

## Cooperative Shutdown

Cancellation is reliable only when all blocking operations can observe it or be interrupted. A task blocked indefinitely on input may prevent session shutdown even after another task has finished.

Possible mechanisms include:

- bounded read timeouts;
- closing the underlying input source;
- cancellation-aware waits;
- explicit wake-up events.

## Cleanup Ordering

A predictable shutdown sequence is:

```text
request stop
    -> stop accepting new input
    -> interrupt or close active operations
    -> drain or discard output according to policy
    -> restore terminal state
    -> close transport
    -> report final result
```

Cleanup should run for normal completion, exceptions, interrupts, and EOF.

## Timeout Restoration

Temporary timeouts should be restored even when an operation fails. Leaving a modified timeout in place can cause later commands to fail unexpectedly.

Use a structured cleanup mechanism rather than relying on the success path.

## Verification Strategy

Test:

1. normal command completion;
2. operator interrupt;
3. operator EOF;
4. remote disconnect;
5. transport error;
6. timeout;
7. output arriving during cancellation;
8. repeated close;
9. terminal-state restoration;
10. no new input after cancellation.

## Conclusion

Interactive cancellation is a lifecycle problem across multiple concurrent activities. Reliable behavior requires shared cancellation state, interruptible waits, deterministic cleanup, and preservation of the original termination cause.

The central design rule is:

> Cancellation is complete only when every activity that can keep the session alive has stopped or been closed.
