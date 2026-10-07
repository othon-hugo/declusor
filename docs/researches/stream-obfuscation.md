# Stream Obfuscation

## Central Question

How can a byte stream be transformed and restored consistently across independent chunks, and what does that transformation fail to protect?

## Scope

This research covers:

- reversible transformations over bytes;
- stateless and stateful transformations;
- maintaining position across chunks;
- synchronization after partial reads and writes;
- distinction between obfuscation and cryptographic protection;
- validation of transformation symmetry.

It does not cover message framing, authentication, key exchange, encryption algorithms, compression, or access control.

## What Obfuscation Changes

Obfuscation changes the representation of bytes so that the transformed stream is less recognizable or less directly readable.

A reversible transformation has two operations:

```text
original bytes -> transform -> obfuscated bytes
obfuscated bytes -> inverse transform -> original bytes
```

For a valid transformation:

```text
inverse(transform(data)) == data
```

The transformation must be applied consistently by both endpoints.

## Obfuscation Is Not Confidentiality

Obfuscation is not automatically encryption.

A simple reversible transformation may hide readable patterns from casual inspection while still being easy to recover. It may provide no guarantees for:

- confidentiality;
- authenticity;
- integrity;
- replay prevention;
- resistance to known-plaintext analysis;
- resistance to statistical analysis.

A transformed payload should not be considered protected merely because it is no longer readable as plain text.

## Stateless Transformations

A stateless transformation processes each byte independently of its position in the stream.

An XOR operation with a repeated mask is a simple example:

```python
def xor_bytes(data: bytes, key: bytes) -> bytes:
    if not key:
        raise ValueError("key must not be empty")

    return bytes(value ^ key[index % len(key)] for index, value in enumerate(data))
```

Applying the same operation twice restores the original bytes:

```python
encoded = xor_bytes(data, key)
decoded = xor_bytes(encoded, key)

assert decoded == data
```

This property exists because XOR is its own inverse. It does not imply that the transformation is secure.

## Chunking Problem

A stream may be transformed in chunks rather than as one complete byte sequence.

For a repeated-mask transformation, resetting the mask index for every chunk changes the result:

```python
encoded = xor_bytes(first_chunk, key) + xor_bytes(second_chunk, key)
```

This is generally not equivalent to transforming the complete stream:

```python
encoded = xor_bytes(first_chunk + second_chunk, key)
```

The second chunk must continue from the correct position in the transformation sequence.

## Stateful Position Tracking

A stateful stream transform preserves its position between calls:

```python
class XorStream:
    def __init__(self, key: bytes) -> None:
        if not key:
            raise ValueError("key must not be empty")

        self._key = key
        self._offset = 0

    def transform(self, data: bytes) -> bytes:
        result = bytes(value ^ self._key[(self._offset + index) % len(self._key)] for index, value in enumerate(data))
        self._offset += len(data)
        return result
```

The sender and receiver must maintain equivalent offsets. If one side resets or skips bytes, all subsequent data may be transformed incorrectly.

## Independent Directions

Bidirectional communication should not assume that both directions share one transformation state.

A safer design gives each direction its own state:

```text
sender -> receiver: outgoing transform state
receiver -> sender: outgoing transform state
```

This prevents reads from one direction from changing the position used for writes in the other direction.

The implementation should define whether state is:

- shared by both directions;
- independent per direction;
- reset for every message;
- reset only when a session starts.

Ambiguous state ownership is a common source of desynchronization.

## Framing Must Remain Independent

Obfuscation transforms bytes. Framing identifies where messages begin and end.

These concerns must not be mixed implicitly.

A typical processing order is:

```text
payload -> frame -> transform -> byte stream
byte stream -> inverse transform -> frame parser -> payload
```

Another protocol may transform only the payload:

```text
payload -> transform -> frame -> byte stream
byte stream -> frame parser -> inverse transform -> payload
```

Both designs can work, but the order must be explicit. Applying the inverse operations in the wrong order produces invalid data or invalid frame boundaries.

## Partial Reads and Writes

A transform layer must support arbitrary chunk boundaries.

The following inputs should produce the same restored output:

```text
[complete stream]
[first byte][remaining bytes]
[small chunks][small chunks][small chunks]
```

The transport may return fewer bytes than requested or combine multiple writes. Transformation correctness cannot depend on a one-write/one-read relationship.

## Empty Data

The transformation should define behavior for an empty chunk:

```python
assert transform(b"") == b""
```

An empty input must not accidentally advance the transformation offset unless the protocol explicitly defines empty frames as consuming state.

This distinction matters when the transform is stateful.

## Reset Conditions

State must be reset at a well-defined lifecycle boundary, such as:

- connection creation;
- handshake completion;
- session restart;
- explicit rekeying;
- connection closure.

Resetting too early causes the endpoints to diverge. Failing to reset may reuse state across logically separate sessions.

A protocol should document whether reconnecting starts a fresh transform state or resumes an existing one.

## Error Detection

A reversible obfuscation transform may restore incorrect bytes without detecting the error.

For example, if one byte is lost from a stateful stream, the inverse transform may continue producing output while using the wrong offset for every following byte.

Obfuscation alone does not provide reliable error detection. A separate integrity mechanism is required when corruption or tampering must be detected.

## Performance Considerations

A byte-wise transform may introduce:

- CPU cost proportional to payload size;
- additional memory for temporary output buffers;
- state management overhead;
- reduced opportunities for zero-copy processing.

Measurements should distinguish:

- transformation time;
- allocation cost;
- transport time;
- framing overhead.

A transformation that is cheap for one large buffer may behave differently when applied to many small chunks.

## Verification Strategy

A transform should be tested with:

1. empty input;
2. one-byte input;
3. repeated bytes;
4. arbitrary binary values;
5. a key of length one;
6. a key longer than the payload;
7. payload lengths that are not multiples of the key length;
8. one complete chunk;
9. many uneven chunks;
10. independent send and receive directions;
11. reset behavior;
12. invalid configuration such as an empty key.

Example:

```python
key = b"key"
data = bytes(range(256))

whole = XorStream(key)
encoded = whole.transform(data)

restored = XorStream(key).transform(encoded)
assert restored == data
```

Chunk-boundary testing should compare complete-stream and split-stream behavior:

```python
sender = XorStream(key)
encoded_parts = [
    sender.transform(data[:3]),
    sender.transform(data[3:17]),
    sender.transform(data[17:]),
]

receiver = XorStream(key)
restored = b"".join(receiver.transform(part) for part in encoded_parts)

assert restored == data
```

## Failure Modes

Common failures include:

- resetting the mask index for every chunk;
- using one shared state for both directions unintentionally;
- applying transformation before framing on one side and after framing on the other;
- advancing state for bytes that were not actually transmitted;
- failing to reset state after reconnecting;
- assuming that transformation detects corruption;
- treating a reversible mask as encryption.

Each failure should have a defined detection or recovery strategy.

## Selection Criteria

A simple reversible transformation may be sufficient when:

- the goal is representation change rather than secrecy;
- both endpoints are controlled;
- framing and integrity are provided separately;
- the transformation is easy to test and reason about.

A stronger cryptographic construction is required when the goal includes:

- confidentiality;
- authentication;
- tamper detection;
- replay resistance;
- protection against observers with known plaintext.

Choosing a stronger construction is not an extension of this research; it is a separate cryptographic design problem.

## Conclusion

Stream obfuscation is a byte transformation with a synchronization requirement. Its most important implementation property is that both endpoints maintain the same transformation state across arbitrary chunk boundaries.

The central design rule is:

> A reversible transformation can hide representation, but only a separately designed security mechanism can establish confidentiality and integrity.
