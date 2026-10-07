# Measuring Python Payload Size

## Central Question

How should different Python payload representations be measured to compare size, preparation cost, and transmission cost fairly?

## Scope

This research covers:

- source size;
- transformed source size;
- compiled code-object size;
- serialized payload size;
- encoding overhead;
- preparation and transmission measurements;
- reproducible benchmark design.

It does not explain AST transformation, compiler optimization, `marshal` compatibility, compression algorithms, or network protocol design.

## Representations to Compare

A benchmark should distinguish at least these representations:

1. Original source text.
2. Filtered or sanitized source text.
3. Compiled code object serialized into bytes.
4. Encoded serialized payload.
5. Complete transport envelope, when one exists.

These representations are not interchangeable. Comparing only their raw byte lengths can produce misleading conclusions.

## Raw Source Size

Source size is measured after encoding it into the format used for transmission:

```python
source_bytes = source.encode("utf-8")
source_size = len(source_bytes)
```

Character count is not a reliable substitute for byte count:

```python
text = "ação"
assert len(text) == 4
assert len(text.encode("utf-8")) == 5
```

The transport cost should therefore be based on encoded bytes, not on the number of source characters.

## Transformed Source Size

A transformed source representation should be encoded using the same encoding as the original:

```python
transformed_bytes = transformed_source.encode("utf-8")
transformed_size = len(transformed_bytes)
```

The size difference can be calculated as:

```python
reduction = original_size - transformed_size
percentage = reduction / original_size * 100
```

The percentage is meaningful only when both values represent the same stage of the pipeline.

## Serialized Code Object Size

A compiled code object can be serialized into bytes:

```python
import marshal

code = compile(source, "<input>", "exec")
serialized = marshal.dumps(code)
serialized_size = len(serialized)
```

This result should be compared with the encoded source representation, not with the source's character count.

The serialized form may be smaller or larger depending on:

- amount of repeated text;
- constants;
- identifiers;
- nested functions;
- line metadata;
- compiler behavior;
- optimization level;
- serialization format.

## Encoding Overhead

A binary payload may be encoded before being placed inside a text-compatible wrapper.

For hexadecimal encoding:

```python
encoded = serialized.hex().encode("ascii")
```

Every input byte becomes two hexadecimal characters:

```python
assert len(encoded) == len(serialized) * 2
```

Base64 has different expansion characteristics:

```python
import base64

encoded = base64.b64encode(serialized)
```

The benchmark must measure the encoded representation if that is what crosses the transport boundary.

## Envelope Overhead

A complete payload may include:

- command metadata;
- operation identifiers;
- channel identifiers;
- length fields;
- delimiters;
- authentication data;
- wrappers;
- escaping;
- padding.

The benchmark should report both:

```text
payload bytes
envelope bytes
total transmitted bytes
```

Otherwise, a small payload may appear efficient while its wrapper dominates the actual cost.

## Preparation Cost

Payload size is only one metric. A representation may reduce transmission cost while increasing local preparation time.

Measure separately:

- parsing time;
- transformation time;
- compilation time;
- serialization time;
- encoding time;
- total preparation time.

Example:

```python
from time import perf_counter

started = perf_counter()

transformed = transform(source)
compiled = compile(transformed, "<input>", "exec")
serialized = serialize(compiled)
encoded = serialized.hex().encode("ascii")

elapsed = perf_counter() - started
```

The benchmark should avoid combining all operations into a single unexplained number.

## Transmission Cost

A controlled benchmark can estimate transmission time from payload size and a fixed simulated bandwidth:

```python
def estimated_time(size: int, bytes_per_second: int) -> float:
    return size / bytes_per_second
```

For real network measurements, record:

- payload size;
- number of writes;
- number of frames;
- transfer duration;
- retransmissions, if observable;
- receiver processing time.

A single timing run is not sufficient. Results should use repeated samples and report median or percentile values.

## Benchmark Dataset

A representative dataset should contain more than one source shape:

- short script with little documentation;
- source with large comments;
- source with long docstrings;
- source with many annotations;
- source with assertions;
- source with many constants;
- nested functions and classes;
- strings containing repetitive text;
- source containing non-ASCII characters.

A benchmark based on a single script cannot establish a general conclusion.

## Correctness Check

Every transformed or serialized representation must be validated before measuring performance:

```python
namespace_original: dict[str, object] = {}
namespace_transformed: dict[str, object] = {}

exec(source, namespace_original)
exec(transformed_source, namespace_transformed)

assert namespace_original["result"] == namespace_transformed["result"]
```

The comparison must use behavior relevant to the program rather than only checking that execution completed.

A smaller payload is not an improvement if the transformation changes required behavior.

## Recommended Result Table

A useful report should include:

| Representation          | Payload bytes | Envelope bytes | Preparation time | Execution result |
| :---------------------- | ------------: | -------------: | ---------------: | :--------------- |
| Original source         |               |                |                  |                  |
| Transformed source      |               |                |                  |                  |
| Serialized code         |               |                |                  |                  |
| Encoded serialized code |               |                |                  |                  |

The table should identify the runtime and settings used for each result.

## Reproducibility

A benchmark must record:

- interpreter implementation;
- interpreter version;
- operating system;
- optimization settings;
- serialization format;
- text encoding;
- encoding scheme;
- compression settings;
- dataset version;
- number of repetitions;
- measurement units.

Without this information, results may not be comparable across environments.

## Common Measurement Errors

### Comparing Characters With Bytes

Character counts ignore encoding overhead.

### Ignoring Wrapper Expansion

Measuring only the inner payload hides the cost of quoting, escaping, hexadecimal encoding, or framing.

### Measuring One Run

One run is affected by startup cost, filesystem state, CPU scheduling, and caching.

### Measuring Preparation and Transfer Together

A result may appear faster because it transfers fewer bytes while spending much longer preparing them.

### Ignoring Correctness

A smaller payload that no longer performs the required operation is not an optimization.

### Mixing Runtime Versions

Different interpreter versions may produce different code-object sizes and timings.

## Suggested Benchmark Procedure

1. Prepare a fixed source dataset.
2. Encode original source into transmission bytes.
3. Produce any transformed representation.
4. Validate transformed behavior.
5. Compile and serialize where applicable.
6. Encode the resulting bytes.
7. Add representative envelope overhead.
8. Measure preparation time separately.
9. Repeat each measurement multiple times.
10. Report size, timing, environment, and correctness together.

## Interpretation

Payload size should be evaluated against the intended constraint:

- bandwidth-limited transmission;
- latency-sensitive execution;
- memory-limited receiver;
- CPU-limited preparation;
- compatibility across runtimes;
- inspectability and debugging requirements.

There is no universally best representation.

A smaller serialized payload may be unsuitable when portability matters. A larger source payload may be preferable when it avoids compatibility failures or makes debugging possible.

## Conclusion

Payload benchmarking is a measurement problem, not a compression claim. A fair comparison must measure the actual transmitted representation, include envelope overhead, separate preparation from transfer, and verify behavior before drawing conclusions.

The central design rule is:

> Optimize the complete delivery path, not an isolated byte count.
