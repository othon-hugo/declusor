# Parallel Session Isolation

## Central Question

How can multiple sessions send and receive data concurrently without mixing bytes, state, results, cancellation, or failures between them?

## Scope

This research covers:

- independent session data paths;
- concurrent reads and writes;
- buffer and response ownership;
- demultiplexing of interleaved activity;
- failure isolation;
- backpressure and fairness between sessions.

It does not cover session hierarchy, resource ownership policy, framing algorithms, authentication, encryption, or process-level sandboxing.

## Hypothesis

Sessions remain isolated during concurrent operation when each session has an explicit identity, independent input and output state, controlled access to shared transport resources, and a dispatch rule that binds every response and failure to exactly one session.

The hypothesis is false if activity from one session can be delivered to another session, if one session can consume another's bytes, or if one session's failure silently changes another session's state.

## Control Plane and Data Plane

A session manager usually has two different responsibilities:

```text
control plane: create, pause, resume, cancel, and close sessions
data plane:    send, receive, buffer, route, and deliver bytes
```

Control operations may be shared by the session manager, but data belonging to a session must remain associated with that session until it reaches the intended consumer.

A lifecycle event should not be inferred from arbitrary data, and data should not be routed by timing or arrival order alone.

## Session Identity

Every concurrent operation needs an unambiguous session identifier:

```text
(session_id, direction, sequence, payload)
```

The identifier may be explicit in a multiplexed protocol or implicit in a dedicated connection. Either way, the routing layer must be able to determine which session owns each result.

Identifiers should not be reused while old buffered data can still arrive. Reuse can cause late data from a previous session to be delivered to a new session.

## Independent State

At minimum, each session should have separate state for:

- inbound buffering;
- outbound queueing;
- response correlation;
- sequence tracking;
- pending operations;
- cancellation state;
- terminal status;
- diagnostics and result delivery.

A shared transport may be acceptable. Shared mutable session state is safe only when ownership and synchronization are explicit.

## Concurrent Reads

A byte stream generally has one ordered read sequence. Multiple independent readers cannot safely consume the same stream without a demultiplexing layer.

Unsafe model:

```text
session A reader ----+
                     +--> one shared byte stream
session B reader ----+
```

One reader may consume bytes intended for the other. A safe model gives the shared stream one reader and routes complete frames or records afterward:

```text
one stream reader -> demultiplexer -> session A queue
                                  -> session B queue
```

If each session has a dedicated connection, each connection can have its own reader. The ownership rule must be explicit.

## Concurrent Writes

Multiple sessions may write concurrently only through a controlled writer or through independent transport paths.

A writer must define whether messages are:

- serialized;
- atomically appended to an output queue;
- split into frames before interleaving;
- allowed to interleave at the byte level.

Byte-level interleaving is unsafe unless the framing and receiver explicitly support it. A complete session message should be enqueued as one routing unit before the transport writes it.

## Response Binding

A response must be bound to the session and operation that produced it:

```text
request(session=A, operation=7)
response(session=A, operation=7)
```

Arrival order is not a reliable correlation key when operations run concurrently. A session should not receive a response merely because it is the next consumer waiting for data.

## Failure Isolation

A failure in one session should produce a controlled transition for that session:

```text
session A failure -> close or fail A
session B          -> remains usable
```

Isolation may be impossible when sessions share a single non-multiplexable connection and that connection fails. In that case, the failure domain must explicitly include every dependent session.

A local session failure should not be widened to the parent transport unless the shared resource can no longer guarantee correct routing.

## Backpressure and Fairness

Independent sessions still compete for shared resources. A session that produces output continuously must not consume all memory, writer capacity, or scheduling time.

The design should define:

- maximum queued bytes per session;
- maximum total queued bytes;
- behavior when a session is slow;
- whether messages are dropped, blocked, or rejected;
- scheduling order;
- fairness between active sessions.

Backpressure is part of isolation because unbounded growth in one session can become a denial of service for all others.

## Minimal Experiment

Create two sessions, `A` and `B`, over a shared in-memory transport or a controlled set of independent transports.

1. Send requests from both sessions concurrently.
2. Interleave their input chunks and response chunks.
3. Use different payload markers so that misrouting is visible.
4. Delay responses from `A` while allowing `B` to complete.
5. Fill `A`'s output queue up to its configured limit.
6. Fail `A` while `B` is active.
7. Reconnect or create a new session using a different identifier.

Expected results:

- `A` receives only responses belonging to `A`.
- `B` receives only responses belonging to `B`.
- Delayed data does not cross session boundaries.
- `A`'s backpressure does not silently corrupt `B`'s data.
- Failing `A` does not close `B` unless they share a failed resource.
- A reused identifier cannot receive stale data from the previous session.

## Verification Strategy

Test at least:

1. independent sessions over independent connections;
2. multiple sessions over one multiplexed connection;
3. partial reads and writes;
4. responses arriving out of order;
5. concurrent writes;
6. one slow consumer;
7. one failed session;
8. shared transport failure;
9. cancellation during delivery;
10. stale data after close and identifier reuse.

Record session identifiers, operation identifiers, queue sizes, terminal transitions, and ownership decisions. Do not rely only on final output; verify that no unexpected cross-session event occurred.

## Failure Modes and Limits

Common failures include:

- multiple readers consuming one stream;
- response routing based on arrival order;
- shared buffers without ownership;
- byte-level interleaving of writes;
- stale data delivered after session reuse;
- one queue growing without a limit;
- one session's exception terminating all sessions accidentally;
- assuming independent sessions remain independent after a shared transport fails.

The strongest isolation guarantee is limited by the narrowest shared resource. Sessions using one physical connection share that connection's availability and failure domain.

## Practical Conclusion

Concurrent session isolation is a data-routing property, not merely a lifecycle property. It requires explicit session identity, independent buffering and correlation state, a single controlled reader or dedicated readers, atomic message writes, bounded queues, and failure-domain rules.

The central design rule is:

> Parallel sessions may share infrastructure, but they must never share ambiguous ownership of bytes or terminal state.
