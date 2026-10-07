# Message Authentication

## Central Question

How can a receiver determine that a message was produced by a party holding the expected secret and was not modified in transit?

## Scope

This research covers message authenticity, integrity, MACs, authenticated tags, verification order, and replay-related metadata.

It does not cover authorization, identity provisioning, key exchange, certificate authorities, encryption algorithms, or access-control policy.

## Authenticity and Integrity

Message authentication answers two related questions:

1. Was the message created by a party that knows the authentication secret?
2. Did the message change after authentication data was generated?

A successful authentication check does not by itself decide whether the authenticated party is authorized to perform an operation.

## MAC Model

A message authentication code uses a shared secret:

```text
sender:   tag = MAC(secret, context || message)
receiver: verify tag using secret and the same context
```

The receiver must reject the message when the tag does not match.

A MAC does not reveal the secret to the receiver's caller, but both endpoints must possess the same secret. This creates a key-management requirement outside the message parser.

## Authenticate the Complete Context

The authenticated input should include every field whose modification would change the meaning of the message:

```text
context || type || sequence || length || payload
```

Authenticating only the payload can permit an attacker to modify metadata such as:

- operation type;
- channel;
- sequence number;
- declared length;
- session identifier.

The exact canonical representation must be identical at both endpoints.

## Verification Before Processing

Authentication should be verified before the message is interpreted or executed:

```text
receive bytes
    -> parse bounded envelope
    -> verify authentication tag
    -> check freshness
    -> dispatch message
```

Parsing may be necessary to locate the tag, but unauthenticated fields must not trigger side effects or expensive unbounded work.

## Constant-Time Comparison

Authentication tags should be compared with a constant-time comparison operation where available:

```python
import hmac

if not hmac.compare_digest(expected_tag, received_tag):
    raise ValueError("invalid authentication tag")
```

A normal equality comparison may reveal information through timing differences in some environments.

## Replay Considerations

A valid authenticated message may still be an old message copied by an observer.

Freshness can be represented by:

- monotonically increasing sequence numbers;
- unique nonces;
- timestamps with an accepted window;
- session-specific counters.

Freshness metadata must itself be authenticated.

A receiver must define whether duplicate sequence numbers are rejected, tolerated, or idempotently processed.

## Failure Behavior

Authentication failure should not reveal unnecessary details such as whether the key, payload, or sequence number was almost correct.

The system should define:

- whether the connection is closed;
- whether the failure is logged;
- whether retries are allowed;
- whether repeated failures trigger throttling;
- whether malformed and invalidly authenticated messages share an external response.

## Verification Strategy

Test:

1. valid message and valid tag;
2. changed payload;
3. changed type or metadata;
4. changed length;
5. changed sequence number;
6. wrong secret;
7. truncated tag;
8. duplicated message;
9. reordered message;
10. constant-time tag comparison;
11. failure before dispatch.

Example with a keyed digest:

```python
import hashlib
import hmac

secret = b"shared-secret"
message = b"type=1;sequence=4;payload=data"
tag = hmac.new(secret, message, hashlib.sha256).digest()

assert hmac.compare_digest(
    tag,
    hmac.new(secret, message, hashlib.sha256).digest(),
)
```

The example demonstrates a MAC check, not a complete key-management system.

## Common Mistakes

- authenticating only the visible payload;
- checking the tag after executing the message;
- using a predictable or reused freshness value without state management;
- comparing tags with an early-exit operation;
- treating authentication as authorization;
- logging secrets or complete sensitive messages;
- accepting duplicate messages without a replay policy;
- using obfuscation as a substitute for authentication.

## Conclusion

Message authentication binds a message and its relevant metadata to a secret-held identity and detects unauthorized modification. It must be combined with freshness rules, key management, and authorization policy to provide a complete security design.

The central design rule is:

> Authenticate the complete message context before allowing the message to produce effects.
