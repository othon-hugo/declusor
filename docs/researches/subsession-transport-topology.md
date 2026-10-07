# Subsession Transport Topology

## Central Question

Which transport topology allows multiple subsessions to exchange data concurrently while preserving routing, ordering, and failure isolation?

## Scope

This research compares:

- dedicated connections per subsession;
- multiplexed channels over one connection;
- shared transports with independent logical queues;
- routing and demultiplexing responsibilities;
- channel and physical-connection failure domains.

It does not cover framing algorithms, obfuscation, authentication, compression, environment state, or resource ownership policy.

## Hypothesis

A topology is reliable when each subsession has an unambiguous data path, the receiver can route every message to exactly one subsession, ordering guarantees are explicit, and a physical transport failure has a documented impact scope.

The hypothesis fails if a subsession can consume another's bytes, if message ordering is assumed but not guaranteed, or if a channel failure unexpectedly closes unrelated work.

## Dedicated Connections

Each subsession uses its own physical or logical connection:

```text
subsession A -> connection A
subsession B -> connection B
```

Advantages include:

- simple ownership and routing;
- independent readers and writers;
- failure isolation between connections;
- easier per-session limits.

Costs include:

- more connection setup;
- more operating-system resources;
- repeated handshake or metadata overhead;
- more listeners, sockets, or connection state.

A dedicated connection does not eliminate the need for per-session lifecycle and resource rules.

## Multiplexed Connection

Multiple logical channels share one physical connection:

```text
one connection -> channel A
                channel B
                channel C
```

Every frame must carry enough channel identity for a single reader to demultiplex the stream:

```text
(channel_id, sequence, payload)
```

Advantages include:

- fewer physical connections;
- shared setup and transport resources;
- efficient use of one ordered stream;
- explicit logical session identifiers.

Costs include:

- a more complex demultiplexer;
- shared physical failure domain;
- head-of-line blocking risk;
- more complex channel lifecycle.

## Shared Transport With Independent Queues

A transport can expose one physical path while maintaining a queue per subsession:

```text
one reader -> demultiplexer -> queue A -> subsession A
                           -> queue B -> subsession B
```

The transport layer owns the physical reader. Logical consumers read only from their own queue.

Writes should enter a scheduler or writer queue as complete logical messages. Direct byte-level writes from multiple subsessions are unsafe unless the transport contract explicitly supports atomic composition.

## Routing Invariants

A topology should guarantee:

- each message has one destination or an explicit broadcast policy;
- unknown channel identifiers are rejected or handled explicitly;
- a closed channel cannot receive new data;
- late data cannot be delivered to a reused channel identifier;
- response correlation does not depend on arrival order alone;
- one channel's queue cannot consume another channel's bytes.

Routing decisions should be made before application code receives the payload.

## Ordering

Ordering may be defined at several levels:

- physical connection order;
- channel order;
- operation order within a channel;
- cross-channel order.

A shared connection naturally preserves physical byte order, but it does not automatically provide useful ordering across channels. The protocol must state whether messages from different channels may overtake each other.

If a channel requires ordered delivery, sequence numbers or an equivalent rule should detect loss, duplication, and reordering.

## Failure Domains

Failure scope depends on the topology:

| Failure                     | Dedicated connections | Multiplexed connection                     |
| :-------------------------- | :-------------------- | :----------------------------------------- |
| Subsession logic failure    | Usually local         | Usually local if channel state is isolated |
| Channel parser failure      | Local to connection   | May threaten the shared demultiplexer      |
| Physical connection failure | One subsession        | All dependent channels                     |
| Queue limit exceeded        | One queue             | One channel or whole scheduler, by policy  |
| Writer failure              | One connection        | Shared writer may affect all channels      |

A design must not promise independent subsession recovery when all subsessions depend on one physical connection.

## Backpressure

A multiplexed topology should define whether backpressure is:

- per channel;
- per connection;
- global;
- weighted by priority;
- fail-fast for slow consumers.

One channel with an unbounded queue can exhaust resources for every other channel. One slow channel can also create head-of-line blocking if the writer serializes all output behind it.

## Channel Lifecycle

A channel should have an explicit lifecycle independent from the physical connection:

```text
OPENING -> OPEN -> CLOSING -> CLOSED
                    |
                    +-> FAILED
```

Closing one channel should remove it from routing before its identifier can be reused. The physical connection may remain open for other channels.

When the physical connection closes, every dependent channel must receive a terminal event with the shared failure cause.

## Minimal Experiment

Compare two implementations using an in-memory byte transport:

1. Create channels `A` and `B`.
2. Send interleaved requests and responses.
3. Delay `A` while allowing `B` to complete.
4. Split frames at arbitrary byte boundaries.
5. Close `A` while `B` remains active.
6. Exceed `A`'s queue limit.
7. Close the physical transport.
8. Reuse a closed channel identifier only after all stale data is discarded.

Expected results:

- each channel receives only its own messages;
- byte fragmentation does not change routing;
- `B` continues while `A` closes, when the topology permits it;
- queue limits affect the documented scope only;
- physical closure terminates every dependent channel;
- stale data cannot reach a newly opened channel.

## Verification Strategy

Test:

1. one dedicated connection per subsession;
2. multiple channels on one connection;
3. interleaved writes;
4. out-of-order channel responses;
5. partial headers and payloads;
6. unknown channel identifiers;
7. channel closure during delivery;
8. queue overflow;
9. physical transport failure;
10. channel identifier reuse.

Record channel identity, sequence, queue state, connection state, and terminal cause for every emitted event.

## Failure Modes and Limits

Common failures include:

- one reader per logical channel consuming a shared stream;
- routing by arrival order;
- direct concurrent writes interleaving bytes;
- channel identifiers reused before stale data is impossible;
- one channel's queue exhausting global memory;
- parser failure affecting every channel unexpectedly;
- promising channel-level recovery after a physical connection failure;
- assuming cross-channel ordering without specifying it.

A topology cannot provide failure isolation finer than its shared physical and parser components.

## Practical Conclusion

Dedicated connections simplify isolation, while multiplexed connections reduce setup and resource overhead at the cost of stronger routing, scheduling, and failure-domain requirements. The correct choice depends on whether connection efficiency or independent failure recovery is the dominant constraint.

The central design rule is:

> Share a physical transport only when logical ownership, routing, ordering, backpressure, and failure scope are explicit.
