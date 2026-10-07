# Reading Length-Prefixed TLV Frames

## Central Question

How can a receiver read, validate, and dispatch type-length-value frames from a byte stream that may return partial or combined reads?

## Scope

This research covers:

- the type-length-value frame model;
- exact header and body reads;
- partial and combined transport reads;
- maximum frame-size validation;
- channel or type dispatch;
- truncated input and EOF behavior.

It does not cover delimiter framing, obfuscation, encryption, authentication, application command semantics, or a particular wire protocol.

## TLV Model

A TLV frame contains three logical parts:

```text
[type][length][value]
```

The type identifies how the value should be interpreted. The length identifies the number of value bytes that follow. The value contains the frame payload.

A concrete format must define:

- type width;
- length width;
- byte order;
- signed or unsigned length representation;
- maximum value length;
- behavior for unknown types;
- behavior for empty values.

Without these rules, two implementations cannot reliably parse the same byte stream.

## Example Header

The following example uses a one-byte type and a four-byte unsigned big-endian length:

```python
import struct

HEADER_FORMAT = ">BI"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


def encode_frame(frame_type: int, value: bytes) -> bytes:
    header = struct.pack(HEADER_FORMAT, frame_type, len(value))
    return header + value
```

The widths and byte order are illustrative. A real protocol must define them as part of its wire contract.

## Stream Reads Are Partial

A receiver cannot assume that one call returns the requested number of bytes.

A header may arrive as:

```text
read 1: [type]
read 2: [first length bytes]
read 3: [remaining length bytes]
```

The payload may also be split across many reads. Conversely, one read may contain multiple complete frames.

The frame reader must preserve surplus bytes after emitting a complete frame.

## Exact Reads

A helper can repeatedly read until a requested number of bytes is available:

```python
def read_exact(read, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size

    while remaining:
        chunk = read(remaining)
        if not chunk:
            raise EOFError("stream ended before frame was complete")

        chunks.append(chunk)
        remaining -= len(chunk)

    return b"".join(chunks)
```

The helper must distinguish:

- a short read, which is normal;
- an empty read indicating EOF or closure;
- an exception indicating a transport failure.

A short read is not a malformed frame.

## Header Validation Before Body Reading

The receiver should read and validate the fixed-size header before reading the payload body:

```python
MAX_VALUE_SIZE = 64 * 1024 * 1024


def read_frame(read) -> tuple[int, bytes]:
    header = read_exact(read, HEADER_SIZE)
    frame_type, value_size = struct.unpack(HEADER_FORMAT, header)

    if value_size > MAX_VALUE_SIZE:
        raise ValueError("frame exceeds maximum size")

    value = read_exact(read, value_size)
    return frame_type, value
```

The size limit must be checked before allocating a buffer or requesting the body. This prevents a peer from causing an unbounded allocation through a malicious length field.

## Empty Values

A frame with a length of zero is valid only if the protocol permits it:

```text
[type][0]
```

The receiver must distinguish an empty value from a missing value. An empty frame can represent a signal, acknowledgment, heartbeat, or another control event.

The meaning belongs to the type definition, not to the framing layer itself.

## Unknown Types

A receiver should define how to handle an unknown type:

- reject the connection;
- discard the value and continue;
- route it to an extension handler;
- preserve it for a higher layer.

If unknown types can be skipped, the length must still be validated before the value is consumed.

Ignoring the type does not justify ignoring its declared size.

## Frame Dispatch

The framing layer should emit a complete frame without interpreting its application payload:

```python
def dispatch(frame_type: int, value: bytes) -> None:
    if frame_type == 1:
        handle_data(value)
    elif frame_type == 2:
        handle_error(value)
    else:
        handle_unknown(frame_type, value)
```

The type determines the destination. The framing layer should not infer a type from the payload contents.

## Buffering Strategies

There are two common implementation strategies.

### Incremental Exact Reads

The reader obtains the header and body directly from the transport using `read_exact`.

Advantages:

- bounded working memory;
- simple state transitions;
- suitable for blocking stream APIs.

Risks:

- a blocked read may wait indefinitely without a timeout;
- concurrent consumers can corrupt frame boundaries;
- transport cancellation must be handled carefully.

### Buffered Parsing

The reader appends incoming bytes to a buffer and extracts complete frames whenever enough bytes are present.

Advantages:

- handles multiple frames per read naturally;
- works well with non-blocking APIs;
- makes chunk-boundary testing straightforward.

Risks:

- buffer growth must be bounded;
- incomplete headers and bodies require explicit state;
- malformed lengths can retain data indefinitely if not rejected.

Both strategies must produce the same frame sequence for the same byte stream.

## Parser State Machine

A minimal parser has these states:

```text
READ_HEADER
    |
    v
VALIDATE_LENGTH -- invalid --> REJECT
    |
    v
READ_VALUE ----- incomplete --> WAIT_FOR_MORE_BYTES
    |
    v
EMIT_FRAME
    |
    v
READ_HEADER
```

The parser should not emit a frame until the entire declared value has been received.

## EOF Behavior

EOF has different meanings depending on parser state:

- during header read: no new complete frame can begin;
- after a complete frame: the stream ended cleanly after that frame;
- during value read: the current frame is truncated;
- with buffered surplus bytes: the surplus is incomplete data.

A receiver should expose these cases distinctly when callers need to diagnose protocol failures.

## Maximum Frame Size

A maximum frame size protects against:

- memory exhaustion;
- excessive processing time;
- oversized temporary buffers;
- protocol abuse;
- accidental corruption of the length field.

The limit should be applied consistently to:

- inbound frames;
- outbound frames;
- in-memory test transports;
- generated clients;
- proxy or forwarding layers.

A size limit should be expressed in bytes, not characters.

## Integer and Byte-Order Rules

The header format must define whether the length is:

- big-endian or little-endian;
- signed or unsigned;
- fixed-width or variable-width;
- allowed to contain reserved values.

A parser should reject values that cannot be represented by its configured integer format rather than silently wrapping them.

## Verification Strategy

A frame reader should be tested with:

1. one complete frame in one read;
2. a header split at every byte boundary;
3. a body split at every byte boundary;
4. multiple frames in one read;
5. an empty value;
6. the maximum permitted value;
7. an oversized value;
8. an invalid type;
9. EOF before the complete header;
10. EOF after a partial body;
11. surplus bytes after a complete frame;
12. arbitrary binary values.

Example:

```python
frame_a = encode_frame(1, b"alpha")
frame_b = encode_frame(2, b"beta")
stream = frame_a + frame_b

# Feed the stream using several different chunk boundaries.
# Every partition must produce [(1, b"alpha"), (2, b"beta")].
```

The output must depend only on byte order and frame contents, never on transport read boundaries.

## Common Failure Modes

Common implementation errors include:

- treating one read as one frame;
- reading the body before validating its length;
- accepting negative or wrapped lengths;
- allocating based on an unbounded peer-controlled value;
- discarding surplus bytes after a frame;
- interpreting EOF during a body as a successful empty value;
- allowing multiple readers to consume the same stream;
- dispatching based on payload heuristics instead of the type field.

Each error should have a deterministic failure state.

## Separation of Responsibilities

The framing layer should be responsible for:

- reading bytes;
- decoding headers;
- validating lengths;
- reconstructing complete values;
- emitting typed frames.

It should not be responsible for:

- interpreting application commands;
- authenticating peers;
- encrypting or obfuscating bytes;
- deciding user-facing messages;
- executing payloads.

Keeping these responsibilities separate makes the framing parser reusable and testable with an in-memory byte source.

## Conclusion

TLV framing converts a byte stream into typed, bounded messages by combining an explicit type field with an explicit value length. Correctness depends on exact reads, validation before allocation, preservation of surplus bytes, and clear EOF behavior.

The central design rule is:

> A length field is an instruction from the peer, not a trusted allocation size.
