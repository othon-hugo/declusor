# Environment State Partitioning

## Central Question

Which execution state should be shared, copied, or isolated when multiple sessions operate within a common environment?

## Scope

This research covers:

- namespace and variable state;
- imports and module caches;
- working directory and environment values;
- standard input, output, and error streams;
- session-local caches;
- shared, snapshot, and isolated state policies.

It does not cover resource ownership, parent-child lifecycle, transport topology, authentication, or operating-system sandboxing.

## Hypothesis

State partitioning is predictable when every state category has an explicit policy and a session cannot accidentally observe or mutate state outside that policy.

The hypothesis fails when a session observes changes from another session without an explicit sharing rule, when a snapshot contains unsafe shared references, or when state persists after the session is expected to be reset.

## State Categories

Environment state should be classified before choosing a partition policy:

| State              | Questions                                                     |
| :----------------- | :------------------------------------------------------------ |
| Namespace          | Should variables and definitions persist across sessions?     |
| Imports            | Are loaded modules shared or isolated?                        |
| Working directory  | Is path context session-specific?                             |
| Environment values | Can one session change values seen by another?                |
| Streams            | Who owns input, output, and error routing?                    |
| Caches             | Is cached data safe to share or does it contain session data? |
| Temporary state    | When is it created, reset, and discarded?                     |

A single policy for the entire environment is usually too coarse.

## Shared State

Shared state is visible and mutable by multiple sessions:

```text
session A ----+
              +--> shared state
session B ----+
```

This can be efficient when state is immutable, read-only, or intentionally collaborative. Mutable shared state requires synchronization, ownership rules, and a defined visibility model.

Shared state creates risks when:

- one session changes a value another expects to remain stable;
- caches contain session-specific data;
- imports execute initialization with side effects;
- cleanup by one session invalidates another session's state.

## Snapshot State

A snapshot gives a new session a copy of an initial state:

```text
base state -> snapshot A
           -> snapshot B
```

Snapshots provide common initialization while allowing later changes to diverge. A shallow copy may still share nested mutable objects, modules, file handles, locks, or other process resources.

The snapshot policy must specify:

- which values are copied;
- which values remain shared;
- whether copying is shallow or deep;
- how non-copyable values are handled;
- when the snapshot is taken;
- whether later base-state changes are visible.

## Isolated State

Independent state gives each session a fresh environment:

```text
base configuration -> session A state
base configuration -> session B state
```

This reduces accidental interference but can increase memory use and initialization cost. Fresh logical state does not imply process isolation or prevent access to shared external resources.

An isolated state policy must define which values are intentionally inherited at creation time, such as configuration, immutable constants, or read-only dependencies.

## Imports and Caches

Import state deserves separate treatment because module caches can be process-global while names are session-local.

A session may have:

- a private namespace with shared imported module objects;
- a private namespace and private module loader;
- shared immutable modules;
- explicitly resettable module state.

Sharing module objects is unsafe when modules retain mutable global state that affects session behavior.

## Working Directory and Environment

Working directory and environment variables are often process-level state. Changing them from one concurrent session can affect another session unexpectedly.

Safer alternatives include:

- passing an explicit working directory to each operation;
- constructing a per-operation environment mapping;
- avoiding process-global mutation;
- isolating operations in separate processes when global state cannot be avoided.

A session-local view must not be mistaken for a process-global mutation.

## Stream State

Input, output, and error streams need explicit routing:

```text
session A -> output A
session B -> output B
```

Sharing one mutable stream without a multiplexer can interleave bytes and make response ownership ambiguous. Separate logical streams may still use one physical transport if a routing layer preserves session identity.

## Reset Semantics

A reset should define what is removed and what remains:

- variables and definitions;
- imported modules;
- caches;
- current directory;
- environment changes;
- output buffers;
- pending operations;
- error state.

Reset must be atomic from the session's perspective. A partially reset environment can be more difficult to reason about than a failed operation.

## Minimal Experiment

1. Create a base environment containing a variable, an import, a cache entry, and a directory value.
2. Create sessions `A` and `B` using shared, snapshot, and isolated policies.
3. Change each state category from `A`.
4. Observe which changes are visible to `B`.
5. Reset `A` and check whether its state remains observable.
6. Run the same experiment concurrently.

Expected results:

- shared state changes are visible only where explicitly documented;
- snapshot state starts equal and diverges after creation;
- isolated state does not expose unrelated mutable changes;
- reset removes the documented session state;
- stream output remains routed to the producing session.

## Verification Strategy

Test:

1. mutable scalar values;
2. nested mutable objects;
3. module-level state;
4. module caches;
5. working directory changes;
6. environment variable changes;
7. output and error routing;
8. concurrent mutation;
9. reset during an active operation;
10. session creation after base-state changes.

Record the initial state, policy, mutation, observer, and expected visibility for every case.

## Failure Modes and Limits

Common failures include:

- assuming a namespace copy clones all referenced state;
- changing process-global cwd for a session-local operation;
- sharing module caches with mutable global state;
- sharing output streams without correlation;
- resetting state while another operation still references it;
- retaining session data in a global cache;
- treating a fresh namespace as an operating-system sandbox;
- allowing base-state changes to appear nondeterministically.

Partitioning cannot isolate external resources that remain process-global unless their access is also controlled.

## Practical Conclusion

Environment partitioning should be decided per state category, not as one global shared-or-isolated switch. Shared immutable state can reduce cost, snapshots can provide common initialization, and independent state reduces accidental interference. Each choice must define visibility, mutation, reset, and concurrency behavior.

The central design rule is:

> State is isolated only when its ownership, visibility, mutation, and reset rules are explicit.
