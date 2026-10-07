# Session Resource Ownership

## Central Question

How should resources be owned, shared, transferred, and closed when multiple sessions use the same runtime or transport infrastructure?

## Scope

This research covers:

- exclusive and shared resource ownership;
- borrowed resources and leases;
- transfer of ownership;
- reference counting and lifetime rules;
- close ordering and idempotency;
- cleanup after partial initialization.

It does not cover parent-child lifecycle states, data-state partitioning, transport framing, authentication, or process isolation.

## Hypothesis

Resource behavior is predictable when every resource has an explicit owner, shared access has a defined synchronization policy, transfers are atomic, and close behavior distinguishes owner shutdown from borrower release.

The hypothesis fails if a borrower can close a resource it does not own, if the owner closes while active borrowers still require the resource, or if cleanup depends on destruction timing that callers cannot observe.

## Ownership Models

A resource can be managed through several models:

| Model       | Lifetime rule                                                | Typical risk                         |
| :---------- | :----------------------------------------------------------- | :----------------------------------- |
| Exclusive   | One session owns and closes it.                              | Other sessions cannot safely use it. |
| Shared      | Multiple sessions use one managed resource.                  | One user can disrupt others.         |
| Borrowed    | A session uses a resource temporarily but does not close it. | Borrower may retain it too long.     |
| Leased      | Use is valid until an expiration or release event.           | Expired use may race with cleanup.   |
| Transferred | Ownership moves atomically from one session to another.      | Old and new owners may both act.     |

The model should be selected per resource rather than assumed for the whole session.

## Ownership Record

An ownership record should identify:

```text
resource_id
owner_id
borrowers
lifecycle_state
created_at
released_at
```

The record should also state which operations are permitted to owners and borrowers. Possessing a reference is not equivalent to owning the resource.

## Shared Resources

Shared resources require an explicit policy for:

- concurrent reads;
- concurrent writes;
- mutation;
- cancellation;
- errors;
- capacity;
- shutdown.

A resource should not be marked shared merely because multiple sessions can access a reference to it. Sharing is safe only when the resource contract supports the access pattern.

## Borrowing and Leases

A borrower should acquire a lease or scoped handle when resource use must be bounded:

```text
owner creates resource
    -> borrower acquires handle
    -> borrower uses resource
    -> borrower releases handle
    -> owner closes after all required handles release
```

A lease should define what happens when it expires while an operation is active. Silent expiration can leave an operation using a resource after its contract ended.

## Transfer of Ownership

Transfer should be atomic from the perspective of observers:

```text
old owner -> transfer pending -> new owner
```

The old owner must stop creating new operations before the new owner becomes responsible. If transfer fails, exactly one owner should remain authoritative.

Transferring a reference without transferring lifecycle responsibility creates double-close and leak risks.

## Closing Rules

Closing behavior should distinguish:

- owner requests shutdown;
- borrower releases its handle;
- resource reaches natural EOF;
- resource fails unexpectedly;
- parent session terminates;
- all users disconnect.

Close should be idempotent when repeated cleanup is possible. A second close should not reopen, corrupt, or produce an unrelated failure.

A shared resource should not close simply because one borrower finished unless the ownership policy says that borrower controls the resource lifetime.

## Partial Initialization

Resource creation often has multiple stages:

```text
allocate -> configure -> register -> expose
```

Failure at any stage must release resources created by earlier stages. A resource should not become visible to other sessions before it is fully configured and registered.

Cleanup must also handle failure between registration and handle delivery.

## Failure Propagation

A resource failure should be propagated according to dependency:

- fail the owner;
- fail all borrowers that cannot continue;
- preserve unrelated resources;
- prevent new acquisitions;
- retain the original failure cause.

A borrower-specific error should not close a shared resource unless the borrower caused or exposed a resource-wide failure.

## Minimal Experiment

1. Create one resource owned by session `A`.
2. Let session `B` borrow a scoped handle.
3. Close `B`'s handle and verify that `A` remains usable.
4. Close `A` while `B` is active and observe the documented policy.
5. Transfer ownership from `A` to `C` while operations are pending.
6. Inject failure during resource initialization.
7. Repeat close and release operations.

Expected results:

- only the owner can transfer or permanently close the resource;
- borrower release does not close an independently owned resource;
- transfer leaves one authoritative owner;
- initialization failure releases every acquired resource;
- repeated cleanup is deterministic;
- unrelated sessions do not lose resources unexpectedly.

## Verification Strategy

Test:

1. exclusive ownership;
2. multiple borrowers;
3. borrower release;
4. owner close with active borrowers;
5. ownership transfer;
6. lease expiration;
7. concurrent acquire and close;
8. partial initialization failure;
9. shared resource failure;
10. repeated cleanup.

Record owner, borrower, handle, resource state, operation state, and close cause after each transition.

## Failure Modes and Limits

Common failures include:

- closing a borrowed resource;
- two owners existing after a race;
- resource visibility before configuration completes;
- cleanup depending on garbage collection;
- borrower handles surviving owner shutdown without a policy;
- one session's cancellation closing a shared resource;
- leaked resources after partial initialization;
- reference counts updated without synchronization;
- treating a shared reference as permission to mutate.

Ownership rules cannot compensate for an underlying resource that does not support the required concurrency model.

## Practical Conclusion

Session resource management requires explicit ownership, scoped borrowing, atomic transfer, bounded leases, and idempotent cleanup. The lifetime of a shared resource must be independent from the incidental completion of one user unless the contract explicitly couples them.

The central design rule is:

> A reference grants access only when the resource contract grants that access; it does not grant ownership.
