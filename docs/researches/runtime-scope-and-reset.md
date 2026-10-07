# Runtime Scope and Reset

## Central Question

When should a subsession share, clone, recreate, or reset the runtime that executes its operations?

## Scope

This research covers:

- runtime scope per process, parent session, and subsession;
- shared and cloned execution state;
- runtime initialization;
- reset and reuse;
- partial initialization failure;
- cleanup of runtime state.

It does not cover environment-state policy in general, resource ownership, transport topology, authentication, or concurrency scheduling.

## Hypothesis

Runtime behavior is predictable when the lifetime and state boundary of each runtime are explicit, initialization is complete before exposure, reset is atomic, and failed or closed runtimes cannot accept new operations.

The hypothesis fails if one subsession observes another's runtime state without an explicit sharing rule, if reset leaves partial state visible, or if a failed runtime remains usable.

## Runtime Policies

A system may choose among several policies:

| Policy | Behavior                                          | Main trade-off                                     |
| :----- | :------------------------------------------------ | :------------------------------------------------- |
| Shared | All subsessions use one runtime instance.         | Low setup cost, high state coupling.               |
| Cloned | Each subsession starts from a runtime snapshot.   | Common initialization, complex mutable references. |
| New    | Each subsession creates a fresh runtime.          | Strong logical isolation, higher setup cost.       |
| Pooled | Subsessions acquire resettable runtime instances. | Reuse efficiency, reset correctness required.      |

The policy may differ by operation type. A read-only runtime can be shared when mutable state is absent or controlled.

## Runtime Boundary

A runtime boundary should define:

- variables and definitions;
- imported modules;
- caches;
- configuration;
- current execution identity;
- output routing;
- pending operations;
- external handles;
- error state.

A new namespace is not necessarily a new runtime. Modules, caches, handles, and process-global state may still be shared.

## Initialization

Runtime creation should follow an explicit sequence:

```text
allocate -> configure -> initialize -> validate -> expose
```

The runtime must not be visible to a subsession before required initialization succeeds. Initialization should be idempotent or reject repeated initialization clearly.

Dependencies created during initialization must be tracked so that a later failure can release them.

## Cloning

Cloning a runtime requires a policy for each state value:

- immutable values can be shared;
- mutable values may require deep copying;
- module objects may remain process-global;
- open handles should usually not be copied;
- locks and task state must not be copied as active ownership;
- caches may need invalidation or namespacing.

A shallow snapshot can create hidden coupling through nested mutable objects.

## Reset

Reset should define exactly what it removes:

- variables and definitions;
- imports and module state;
- caches;
- temporary files or directories;
- output buffers;
- pending operations;
- errors and cancellation state;
- identity and session metadata.

Reset should not begin while operations can still mutate the runtime unless the runtime supports transactional reset. A reset that fails halfway must produce a terminal or recoverable state, not a silently mixed state.

## Reuse and Pooling

A pooled runtime must be sanitized before reuse:

```text
release -> stop work -> drain operations -> reset state -> validate -> make available
```

A runtime should not return to the pool merely because its primary operation completed. Background tasks, open handles, cached identity, and output buffers may still contain previous-session state.

## Failure and Terminal States

A runtime should distinguish:

- not initialized;
- initializing;
- ready;
- reset requested;
- resetting;
- failed;
- closed.

New work should be rejected in `INITIALIZING`, `RESETTING`, `FAILED`, and `CLOSED` states unless the contract explicitly supports it.

The original initialization or reset failure should remain observable to operators without exposing sensitive internal data.

## Minimal Experiment

1. Create a base runtime containing a variable, import, cache entry, and output buffer.
2. Run one operation that mutates each state category.
3. Create a second subsession using shared, cloned, new, and pooled policies.
4. Observe which values are visible.
5. Reset or release the first runtime.
6. Reuse it for a third subsession.
7. Inject a failure during initialization and during reset.
8. Attempt new work after each failure.

Expected results:

- sharing exposes only explicitly shared state;
- cloning does not share unsafe mutable references;
- new runtimes start from the documented baseline;
- pooled runtimes contain no prior-session state;
- partial initialization and reset failures prevent unsafe reuse;
- terminal runtimes reject new operations.

## Verification Strategy

Test:

1. shared runtime behavior;
2. cloned runtime behavior;
3. fresh runtime behavior;
4. pooled runtime reuse;
5. nested mutable state;
6. module and cache state;
7. reset during active work;
8. initialization failure;
9. reset failure;
10. operation after runtime failure;
11. output and identity cleanup.

Record runtime identity, subsession identity, state before and after reset, active operations, and terminal cause.

## Failure Modes and Limits

Common failures include:

- treating a copied namespace as a complete runtime clone;
- returning a runtime to a pool before background work ends;
- clearing variables but retaining module or cache state;
- exposing a runtime before initialization completes;
- accepting work after reset failure;
- resetting shared state while another subsession uses it;
- copying open handles, locks, or active task state;
- hiding partial cleanup failures.

Logical runtime isolation cannot isolate process-global state or external resources that the runtime can still access.

## Practical Conclusion

Runtime scope should be selected per state and lifecycle requirement. Sharing reduces setup cost, cloning provides common initialization, fresh runtimes reduce coupling, and pooling demands a verified reset contract. Initialization and reset are lifecycle boundaries, not incidental cleanup details.

The central design rule is:

> A runtime is reusable only after its previous state, work, handles, and identity have been explicitly accounted for.
