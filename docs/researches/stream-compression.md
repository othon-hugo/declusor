# Stream Compression

## Central Question

How can a byte stream be compressed and decompressed while preserving message boundaries, bounded resource usage, and predictable failure behavior?

## Scope

This research covers compression placement, streaming state, framing interaction, size measurement, decompression limits, and expansion risks.

It does not cover encryption, authentication, obfuscation, serialization formats, or a specific compression library.

## Compression Changes Representation

Compression maps input bytes to a different representation:

```text
original bytes -> compressor -> compressed bytes
compressed bytes -> decompressor -> original bytes
```

The result depends on the input. Text with repeated patterns may compress substantially, while already compressed or random data may not become smaller.

## Compression and Framing Order

Two common arrangements are:

```text
payload -> compress -> frame -> transport
```

and:

```text
payload -> frame -> compress -> transport
```

Compressing the payload before framing usually preserves independent message boundaries. Compressing an entire stream can achieve better ratios but couples messages to shared compressor state.

The receiver must apply inverse operations in the opposite order.

## Per-Message Compression

Each message is compressed independently:

```text
[compressed length][compressed payload]
[compressed length][compressed payload]
```

Advantages:

- messages can be decompressed independently;
- one corrupted message need not invalidate all later messages;
- retries and parallel processing are easier;
- limits can be applied per message.

Costs include repeated headers and reduced compression ratio for small messages.

## Continuous Stream Compression

A compressor can remain active across multiple messages. Repeated data across message boundaries may then compress better.

This approach introduces shared state:

- the decompressor must receive messages in order;
- one corrupted segment may affect later output;
- reconnecting may require a reset or dictionary transfer;
- message boundaries still need an outer framing rule.

Compression state must not be mistaken for message framing.

## Size Accounting

Measure all relevant sizes:

```text
original payload size
compressed payload size
compression metadata
frame overhead
transport encoding overhead
```

A small input may grow because compressor metadata and framing exceed the original payload size.

The decision to compress should consider a threshold:

```python
if len(payload) < MINIMUM_COMPRESSION_SIZE:
    send_uncompressed(payload)
else:
    send_compressed(payload)
```

The threshold should be based on measurements rather than assumption.

## Decompression Limits

Compressed input can expand significantly during decompression. A receiver should limit:

- compressed input size;
- decompressed output size;
- memory used by dictionaries and buffers;
- CPU time;
- number of decompression operations.

The compressed size alone is not a safe resource bound.

A frame should declare or imply enough metadata for the receiver to enforce an output limit before accepting unbounded expansion.

## Compression Bombs

A small compressed payload may produce a very large output. This can exhaust memory, CPU, or downstream storage.

The receiver should stop decompression when the configured output limit is reached and report a controlled failure.

The limit should apply to both trusted and untrusted input unless the trust boundary explicitly justifies another policy.

## Error Handling

The decompressor should distinguish:

- invalid compressed data;
- truncated compressed data;
- output limit exceeded;
- unsupported compression method;
- checksum failure, when the format provides one;
- transport EOF before the compressed value is complete.

A decompression failure must not be interpreted as an empty payload.

## Flush and Finalization

Streaming compressors often buffer data internally. The sender must define when data is flushed and when the stream is finalized.

A receiver may not be able to emit the final bytes until it observes the end-of-stream marker for that compressed unit.

The protocol must specify whether a frame contains:

- a complete independently compressed value;
- a continuation segment;
- the final segment of a stream.

## Compression and Security

Compression does not provide:

- confidentiality;
- authenticity;
- integrity;
- access control.

Compressing before encryption is common, but the ordering and side-channel implications require a separate security analysis.

Compression should not be used to conceal the meaning of sensitive data.

## Verification Strategy

Test:

1. empty input;
2. very small input;
3. repetitive input;
4. random input;
5. already compressed input;
6. multiple independent messages;
7. continuous stream state;
8. truncated compressed data;
9. invalid compressed data;
10. output limit exceeded;
11. reset and reconnect behavior;
12. compression threshold decisions.

Example round trip:

```python
import zlib

payload = b"repeatable data " * 100
compressed = zlib.compress(payload)
restored = zlib.decompress(compressed)

assert restored == payload
```

The test must also measure cases where compression increases the payload size.

## Common Mistakes

- compressing each transport chunk without preserving message semantics;
- assuming compressed size bounds decompressed size;
- forgetting to flush or finalize the compressor;
- sharing stream state across unrelated sessions;
- retrying a corrupted continuous stream without resetting state;
- compressing data that is already compressed without measuring the cost;
- treating compression as encryption.

## Conclusion

Compression is a representation and resource-management concern. Correct design requires an explicit relationship between compression units and message frames, bounded decompression, and measurements across realistic inputs.

The central design rule is:

> Bound the decompressed result, not only the compressed input.
