# Nonce-Delimited Shell Envelopes

## Central Question

How can a command-oriented shell stream identify the end of each response when payload output is arbitrary text and reads do not preserve message boundaries?

## Scope

This research covers:

- envelopes delimited by a per-message nonce;
- separation of nonce, payload, and terminator;
- fragmented delimiters across reads;
- collision risks from output content;
- logical completion versus transport EOF;
- parser buffering and limits.

It does not cover length-prefixed framing, byte obfuscation, authentication, encryption, command semantics, or a specific shell implementation.

## Envelope Model

A command transaction can be represented as an envelope:

```text
[nonce][separator][payload][separator]
```

The receiver sends or observes a command-specific marker after the command completes:

```text
__END_<nonce>__
```

The receiver treats that marker as the logical end of the response and returns the bytes before it as command output.

The marker must be associated with the current transaction. A fixed marker shared by every command is vulnerable to accidental appearance in normal output.

## Why a Dynamic Nonce Is Useful

A fresh nonce for each transaction reduces the probability that ordinary command output contains the completion marker.

For a uniformly generated $n$-bit nonce, an idealized accidental collision probability is approximately:

$$
P(\text{collision}) = 2^{-n}
$$

This estimate depends on assumptions about nonce generation and output content. It should not be treated as a proof of security or as a replacement for authentication.

A nonce should be:

- unpredictable enough to avoid deliberate guessing;
- unique within the active stream;
- represented in a restricted alphabet;
- bound to exactly one transaction.

## Separator Rules

The envelope must define how the nonce and payload are separated.

A common structure is:

```text
nonce + NUL + payload + NUL
```

This is workable only when the shell-side parser can safely handle NUL boundaries and the payload rules do not reinterpret them.

The protocol must specify:

- separator byte or sequence;
- whether the separator may occur inside payload data;
- how an empty payload is represented;
- whether the nonce is text or binary;
- whether the completion marker includes the separator.

A delimiter that is not unambiguous under the payload rules cannot provide reliable framing.

## Fragmentation Across Reads

The completion marker may be divided across multiple reads:

```text
read 1: output + "__END_12"
read 2: "34__" + remaining bytes
```

A parser that searches only within each individual read can miss the marker.

The receiver must preserve enough suffix data between reads to detect a marker split at any position. A rolling buffer or incremental pattern matcher is required.

The parser must also handle the opposite case:

```text
read 1: marker + next response prefix
```

After extracting one response, surplus bytes must remain available for the next parser state.

## Logical EOF Versus Transport EOF

A nonce marker indicates completion of one command response. It is a logical EOF for that transaction, not necessarily a connection close.

```text
logical EOF: current command is complete
transport EOF: underlying stream has closed
```

The connection may remain available for another command after a logical EOF.

A parser must not close the entire session merely because it observed a command completion marker.

Conversely, transport EOF before the expected marker indicates an incomplete response unless the protocol explicitly permits implicit completion.

## Parser States

A minimal parser can use states such as:

```text
WAIT_FOR_OUTPUT
    |
    v
SEARCH_FOR_MARKER
    |
    +-- marker incomplete --> BUFFER_SUFFIX
    |
    +-- marker found -------> EMIT_RESPONSE
    |
    +-- transport EOF ------> INCOMPLETE_RESPONSE
```

The parser should associate the expected marker with the active transaction. A marker for a previous or unknown transaction must not complete the current response.

## Output That Resembles the Marker

A dynamic nonce reduces accidental collision, but output can still contain arbitrary bytes. Delimiter detection must define its response to a marker-like sequence.

Possible policies include:

- require an exact marker format;
- require a marker followed by a separator or line boundary;
- include transaction metadata in the marker;
- authenticate the completion record separately;
- use length-prefixed framing instead of delimiters.

A marker found inside ordinary output cannot be distinguished from a real completion record unless the protocol provides additional structure.

## Nonce Generation

Nonce generation should use a cryptographically strong random source when deliberate prediction would be harmful:

```python
import secrets

nonce = secrets.token_hex(16)
marker = f"__END_{nonce}__".encode("ascii")
```

The nonce should not be generated from predictable values such as:

- timestamps alone;
- sequential counters alone;
- process identifiers alone;
- command text alone.

Uniqueness and unpredictability are different properties. A counter can provide uniqueness but not unpredictability.

## Per-Transaction Binding

The expected marker should be stored with the active command transaction:

```python
transaction = {
    "nonce": nonce,
    "marker": marker,
    "state": "waiting",
}
```

When the marker is found, the parser should verify that it belongs to the current transaction before emitting a response.

A parser should not accept an arbitrary marker supplied by the incoming stream as proof that the transaction completed.

## Buffering Limits

A missing marker can cause the receiver to retain output indefinitely. The parser therefore needs limits for:

- maximum response size;
- maximum time without a marker;
- maximum marker-search buffer;
- maximum number of incomplete transactions;
- behavior after limit exhaustion.

When a limit is reached, the protocol should produce an explicit failure state rather than silently truncating output.

## Empty Responses

An empty command response should still produce a complete envelope:

```text
[nonce][separator][separator]
```

The parser must distinguish an empty response from:

- no response received yet;
- a truncated envelope;
- a connection that closed before completion.

## Binary Output

A delimiter-based shell envelope is easiest to reason about when command output is text. Arbitrary binary output may contain:

- NUL bytes;
- line terminators;
- partial marker sequences;
- encoding-invalid byte sequences.

If binary output is supported, the protocol must define whether it is:

- escaped;
- encoded before delivery;
- length-prefixed inside the envelope;
- restricted to a safe alphabet.

A text delimiter does not automatically make arbitrary binary data safe.

## Verification Strategy

A parser should be tested with:

1. a marker received in one read;
2. a marker split at every possible byte position;
3. multiple responses received in one read;
4. output containing a near-match to the marker;
5. output containing the complete marker text;
6. an empty response;
7. transport EOF before the marker;
8. a marker for an unexpected transaction;
9. output exceeding the configured limit;
10. binary or non-UTF-8 output when supported.

Example marker-splitting test:

```python
marker = b"__END_abc123__"
stream = b"result" + marker + b"next"

for split in range(len(marker) + 1):
    chunks = [
        stream[: len(b"result") + split],
        stream[len(b"result") + split :],
    ]

    # Feed both chunks to the same incremental parser.
    # The first response must always be b"result".
    pass
```

The result must not depend on the location where the transport split the bytes.

## Failure Modes

Common failures include:

- searching for markers only within individual reads;
- treating transport EOF as command completion;
- accepting a marker from the wrong transaction;
- discarding bytes after a marker;
- buffering indefinitely when a marker is missing;
- using a predictable nonce;
- assuming text output when binary output is possible;
- treating nonce randomness as authentication.

Each failure should have a defined state transition and recovery policy.

## When to Prefer Another Framing Mode

Nonce-delimited envelopes may be unsuitable when:

- payloads are arbitrary binary data;
- strict maximum sizes are required;
- output can be adversarially controlled;
- completion markers cannot be authenticated;
- a length is known before transmission.

Length-prefixed or structured framing may provide clearer boundaries in those cases.

## Conclusion

A nonce-delimited envelope can provide a practical logical end marker for command responses over a byte stream. Its correctness depends on incremental parsing, transaction binding, bounded buffering, and an explicit distinction between logical completion and connection closure.

The central design rule is:

> A dynamic delimiter reduces accidental collisions, but reliable framing still requires stateful parsing and explicit failure handling.
