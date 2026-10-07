# Python `marshal` and Code Object Serialization

## Central Question

When can a compiled Python code object be serialized with `marshal`, and what compatibility and security limits make this approach unsuitable in other situations?

## Scope

This research covers:

- serialization of code objects with `marshal.dumps`;
- deserialization with `marshal.loads`;
- implementation and version compatibility;
- differences between source portability and bytecode portability;
- security risks of loading untrusted data.

It does not cover AST transformations, compiler optimization levels, network framing, compression, encryption, or sandboxing.

## What `marshal` Serializes

Python source can be compiled into a code object:

```python
source = "result = 1 + 2\n"
code = compile(source, "<input>", "exec")
```

The code object can then be serialized:

```python
import marshal

payload = marshal.dumps(code)
```

The serialized value can be reconstructed:

```python
restored = marshal.loads(payload)
```

The restored object can be executed:

```python
namespace: dict[str, object] = {}
exec(restored, namespace)

assert namespace["result"] == 3
```

The serialized payload contains the compiled representation rather than the original source text.

## Source Versus Code Object

Source code is interpreted by the receiving Python runtime:

```python
code = compile(source, "<input>", "exec")
```

A serialized code object is compiled before transmission and reconstructed by the receiving runtime:

```python
code = marshal.loads(payload)
exec(code, namespace)
```

This can reduce repeated compilation work, but it couples the payload to the interpreter format that produced it.

The two approaches have different properties:

| Representation        | Main advantage                    | Main limitation                                  |
| :-------------------- | :-------------------------------- | :----------------------------------------------- |
| Source text           | More portable and inspectable     | Requires parsing and compilation at the receiver |
| Marshaled code object | Ready for execution after loading | Strong dependency on interpreter compatibility   |

## Compatibility

`marshal` is not a stable cross-version bytecode interchange format.

A payload may depend on:

- Python implementation;
- major Python version;
- minor Python version;
- bytecode format;
- compiler behavior;
- marshal format version;
- platform-specific implementation details.

Matching the Python language version alone is not always sufficient. A compatibility policy should identify the actual runtime implementation and version before selecting a code-object payload.

When compatibility is uncertain, transmitting source code is generally safer than transmitting a marshaled code object.

## Code Objects Are Not Long-Term Artifacts

Marshaled code objects should not be treated as durable build artifacts.

They are unsuitable for:

- long-term storage;
- archival formats;
- public interchange;
- guaranteed future compatibility;
- distribution across unknown Python implementations.

A new interpreter release may change the bytecode structure or the assumptions required to execute the code object.

## Security Considerations

`marshal.loads` must not be treated as a safe parser for untrusted input.

A marshaled payload may contain executable code objects. Loading the payload can make that code available for execution, and executing the resulting object can perform any action allowed by the process.

Example:

```python
import marshal

restored = marshal.loads(received_bytes)
exec(restored, {})
```

The payload must therefore be trusted or authenticated before it is loaded and executed.

Serialization does not provide:

- isolation;
- privilege reduction;
- sandboxing;
- malware detection;
- integrity protection;
- confidentiality.

Those properties require separate mechanisms.

## Format Version

`marshal.dumps` accepts a format version:

```python
payload = marshal.dumps(code, version=marshal.version)
```

The format version controls the marshal representation, but it does not eliminate dependency on the Python implementation or bytecode format.

It should not be confused with the Python language version or the interpreter's bytecode magic number.

## Failure Modes

Deserialization can fail when:

- the payload is truncated;
- the payload is not a valid marshal representation;
- the format is unsupported;
- the resulting object contains unsupported structures;
- the producer and receiver use incompatible implementations;
- the payload is not actually a serialized code object.

A system using marshaled code should define a fallback behavior rather than assuming that every payload can be loaded successfully.

## Verification Strategy

A minimal experiment should check:

1. A code object can be serialized.
2. The serialized result is bytes.
3. The payload can be loaded by a compatible interpreter.
4. The restored object executes the expected behavior.
5. A truncated payload fails predictably.
6. An incompatible runtime is rejected before loading.
7. Untrusted payloads are never loaded without authentication.
8. Source fallback remains available when compatibility is uncertain.

Example:

```python
import marshal

source = """
value = 10
result = value * 2
"""

compiled = compile(source, "<input>", "exec")
payload = marshal.dumps(compiled)
restored = marshal.loads(payload)

namespace: dict[str, object] = {}
exec(restored, namespace)

assert namespace["result"] == 20
```

## Recommended Compatibility Policy

A producer should transmit a marshaled code object only when all required compatibility conditions are satisfied.

A conservative policy checks:

- interpreter implementation;
- major Python version;
- minor Python version;
- bytecode compatibility identifier;
- supported marshal format;
- payload integrity.

If any check fails, transmit source code instead.

This is a transport decision, not a property that can be inferred reliably from the payload after transmission.

## When to Prefer Source

Source code is preferable when:

- the receiver's Python version is unknown;
- multiple Python implementations are supported;
- long-term portability matters;
- the payload must be inspectable;
- compatibility negotiation is unavailable;
- the serialized representation cannot be authenticated.

The receiver can compile the source using its own interpreter:

```python
code = compile(source, "<remote>", "exec")
exec(code, namespace)
```

## Conclusion

`marshal` is useful for short-lived exchange of compiled code between compatible Python runtimes. It can avoid recompilation and transmit a ready-to-load representation, but it is not a stable portable bytecode format.

The central design rule is:

> Serialize code objects only inside a controlled compatibility boundary, and never treat `marshal.loads` as a trust boundary.
