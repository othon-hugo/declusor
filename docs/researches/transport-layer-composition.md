# Composing Transport Layers

## Central Question

How can byte-stream transport layers be composed without changing ordering, lifecycle, or partial-read semantics?

## Scope

This research covers decorator-style transport composition, delegation, lifecycle propagation, independent read/write behavior, and failure handling.

It does not cover a specific obfuscation algorithm, message framing, authentication, encryption, or application commands.

## Layer Model

A composed transport can be represented as:

```text
application -> outer layer -> inner layer -> physical transport
```

Each layer should expose the same essential byte-stream contract to the layer above it.

## Delegation

A wrapper normally delegates operations it does not transform:

```python
class Layer:
    def __init__(self, inner):
        self._inner = inner

    def close(self) -> None:
        self._inner.close()
```

Delegation must preserve return values, exceptions, timeouts, endpoint information, and lifecycle state according to the contract.

## Ordering

When layers transform bytes, order matters:

```text
payload -> framing -> transformation -> transport
```

The receiver must apply inverse operations in reverse order. Reordering layers can produce invalid frames or data that cannot be restored.

## Independent Directions

Read and write paths may require separate state. A write-side transform should not advance a read-side cursor unless the contract explicitly requires shared state.

```text
write state: application -> transport
read state:  transport -> application
```

This is especially important for stateful transforms and concurrent bidirectional sessions.

## Lifecycle

Closing the outer layer should eventually close resources owned by inner layers. Repeated close calls should have defined behavior.

A layer should define how it propagates:

- open;
- initialization;
- shutdown;
- timeout changes;
- cancellation;
- transport errors.

## Failure Propagation

A wrapper should not silently convert a transport failure into a successful empty read. Errors must preserve enough context for the caller to distinguish:

- temporary unavailability;
- clean EOF;
- protocol failure;
- local cancellation;
- remote closure.

## Verification Strategy

Test:

1. one layer and multiple layers;
2. read and write ordering;
3. partial chunks;
4. timeout delegation;
5. close propagation;
6. repeated close;
7. inner-layer failure;
8. independent direction state;
9. compatibility with an in-memory transport.

## Conclusion

Transport composition is safe when every layer preserves the byte-stream contract and makes its transformation, state, and lifecycle responsibilities explicit.

The central design rule is:

> A wrapper may change bytes, but it must not silently change the stream contract.
