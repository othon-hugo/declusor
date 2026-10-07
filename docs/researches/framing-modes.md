# Message Framing Modes

## Central Question

How can a byte stream be divided into complete messages when the underlying transport does not preserve message boundaries?

## Scope

This research covers:

- the difference between streams and messages;
- delimiter-based framing;
- length-prefixed framing;
- fixed-size framing;
- self-describing record framing;
- failure modes and selection criteria.

It does not cover encryption, obfuscation, authentication, compression, application semantics, or a specific network library.

## Streams Do Not Preserve Writes

A byte-stream transport exposes an ordered sequence of bytes. It does not guarantee that one write at the sender corresponds to one read at the receiver.

A message sent in one operation may be received as:

- several smaller chunks;
- one complete chunk;
- several messages combined in one chunk;
- a combination of partial and complete messages.

A receiver must therefore maintain a buffer and apply an explicit framing rule.

```text
sender writes:  [message A][message B]
receiver reads: [message A prefix]
                [message A remainder][message B prefix]
                [message B remainder]
```

The framing layer is responsible for reconstructing complete messages before handing them to the application.

## Delimiter-Based Framing

A delimiter marks the end of a message:

```text
message A <DELIMITER> message B <DELIMITER>
```

A receiver searches for the delimiter, extracts the bytes before it, and retains any remaining bytes for the next message.

### Advantages

- simple to inspect and debug;
- works well for text-oriented payloads;
- message size does not need to be known in advance;
- a complete message can be streamed incrementally.

### Risks

- the delimiter may occur inside the payload;
- escaping or encoding may be required;
- a delimiter split across reads must still be detected;
- a missing delimiter can cause unbounded buffering;
- binary payloads are inconvenient without an escaping policy.

A delimiter must be unambiguous under the payload rules. A random or dynamic delimiter reduces accidental collisions but does not eliminate the need for bounded buffering and timeout handling.

## Length-Prefixed Framing

A length prefix declares the number of payload bytes:

```text
[length][payload]
```

The receiver first reads the fixed-size header, decodes the length, validates it, and then reads exactly that many payload bytes.

Example with a four-byte unsigned big-endian length:

```python
import struct

header = struct.pack(">I", len(payload))
frame = header + payload
```

The receiver must not allocate or read the declared body before checking that the length is valid.

### Advantages

- supports arbitrary binary payloads;
- does not require escaping payload content;
- permits exact payload boundaries;
- works efficiently with incremental reads.

### Risks

- corrupted lengths can desynchronize the stream;
- oversized lengths can cause memory exhaustion;
- truncated bodies must be detected;
- integer encoding and byte order must be specified;
- the header itself may be incomplete.

Every length-prefixed protocol needs a maximum frame size and a defined response to invalid lengths.

## Fixed-Size Framing

Every message has the same size:

```text
[record 1][record 2][record 3]
```

The receiver can calculate message boundaries from the position in the stream.

### Advantages

- minimal framing overhead;
- simple parsing;
- predictable memory requirements;
- useful for small, uniform records.

### Risks

- inefficient for variable-size data;
- padding may be required;
- a single lost or inserted byte can misalign all following records;
- payload size must be known and enforced.

Fixed-size framing is appropriate only when the message structure naturally has a stable width.

## Self-Describing Records

A record may contain multiple fields, each with its own type and length:

```text
[record header][field header][field data]...
```

This approach can represent optional fields and multiple data types while keeping boundaries explicit.

### Advantages

- supports structured binary data;
- fields can be added with compatibility rules;
- individual fields can be skipped when their type is unknown;
- payload boundaries remain explicit.

### Risks

- more complex parser and validation rules;
- every nested length needs a bound;
- unknown fields require a defined policy;
- malformed nesting can create ambiguous or expensive parsing paths.

Self-describing framing should specify field types, lengths, byte order, nesting limits, and unknown-field behavior.

## Comparison

| Mode            | Best suited for               | Main risk                   | Required protection                                |
| :-------------- | :---------------------------- | :-------------------------- | :------------------------------------------------- |
| Delimiter       | Text or line-like messages    | Delimiter collision         | Escaping, encoding, or collision-resistant markers |
| Length-prefixed | Arbitrary binary payloads     | Invalid or oversized length | Maximum size and exact reads                       |
| Fixed-size      | Uniform records               | Stream misalignment         | Fixed width and strict validation                  |
| Self-describing | Structured extensible records | Nested parsing complexity   | Type, length, and nesting limits                   |

## Receiver State Machine

A framing parser should have explicit states. For length-prefixed messages, a minimal state machine is:

```text
READ_HEADER
    |
    v
VALIDATE_LENGTH -- invalid --> REJECT
    |
    v
READ_BODY ------ incomplete --> WAIT_FOR_MORE_BYTES
    |
    v
EMIT_MESSAGE
    |
    v
READ_HEADER
```

The parser should not treat an incomplete read as an empty message or a connection failure unless the transport has definitively reached EOF.

## Buffering Rules

A receiver should define:

- maximum buffer size;
- maximum message size;
- behavior when a delimiter is absent;
- behavior when a body is truncated;
- timeout while waiting for more bytes;
- handling of multiple messages in one read;
- handling of surplus bytes after a complete message.

Without these rules, malformed input can cause memory growth or permanent parser blockage.

## Framing and Transport Are Separate

Framing defines message boundaries. The transport defines how bytes move.

The same framing strategy can run over:

- a TCP connection;
- a pipe;
- a file-like stream;
- an in-memory duplex channel;
- another ordered byte-stream abstraction.

A framing parser should not rely on the size or timing of transport reads.

## Minimal Length-Prefix Example

```python
import struct

HEADER_SIZE = 4
MAX_FRAME_SIZE = 1024 * 1024


def parse_frames(buffer: bytearray) -> list[bytes]:
    frames: list[bytes] = []

    while len(buffer) >= HEADER_SIZE:
        length = struct.unpack(">I", buffer[:HEADER_SIZE])[0]

        if length > MAX_FRAME_SIZE:
            raise ValueError("frame exceeds maximum size")

        total_size = HEADER_SIZE + length
        if len(buffer) < total_size:
            break

        frames.append(bytes(buffer[HEADER_SIZE:total_size]))
        del buffer[:total_size]

    return frames
```

This parser deliberately keeps incomplete bytes in the buffer and can emit multiple frames from one input chunk.

A production implementation must also define behavior for EOF, malformed headers, timeouts, and allocation limits.

## Verification Strategy

A framing implementation should be tested with:

1. one complete message in one read;
2. one message split across many reads;
3. multiple messages in one read;
4. a partial header;
5. a partial body;
6. an empty payload;
7. the maximum permitted payload;
8. an oversized payload;
9. malformed delimiter or length data;
10. EOF before a complete message.

A useful test feeds the same bytes using different chunk boundaries and verifies that the emitted messages are identical.

```python
payload = b"alpha" + b"beta"
expected = [b"alpha", b"beta"]

for chunks in (
    [payload],
    [payload[:1], payload[1:]],
    [payload[:3], payload[3:4], payload[4:]],
):
    # Feed chunks into the same parser and compare emitted messages.
    pass
```

The important property is independence from transport read boundaries.

## Selection Criteria

Choose delimiter framing when:

- payloads are text-oriented;
- a reliable escaping rule exists;
- human inspection is valuable;
- the maximum message size is easy to enforce.

Choose length-prefixed framing when:

- payloads may contain arbitrary binary data;
- exact message lengths are available;
- strict size validation can be implemented.

Choose fixed-size framing when:

- records have a stable size;
- low overhead matters;
- misalignment can be detected and recovered from.

Choose self-describing records when:

- messages contain structured fields;
- extensibility is required;
- the additional parsing complexity is justified.

## Conclusion

Framing is the mechanism that converts an ordered byte stream into complete messages. Its correctness depends on explicit boundaries, buffering, validation, and behavior under partial input.

The central design rule is:

> A framing parser must reconstruct messages from bytes, never from assumptions about how the sender performed its writes.
