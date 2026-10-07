# Operation Code Dispatch

## Central Question

How can abstract operations be dispatched to different runtimes without embedding transport-specific logic in command handlers?

## Scope

This research covers operation identifiers, command-to-operation translation, renderer boundaries, and unknown-operation handling.

It does not cover framing, transport composition, plugin discovery, asset resolution, or execution security.

## Abstract Operations

An operation describes intent independently of its wire representation:

```text
EXECUTE_COMMAND
EXECUTE_CODE
LOAD_MODULE
STORE_FILE
EXECUTE_FILE
```

The operation identifier should be stable enough for the receiving runtime to select the correct behavior.

## Translation Boundary

A command handler should produce a structured operation:

```python
operation = Operation(
    code=OperationCode.EXECUTE_COMMAND,
    arguments={"command": command},
)
```

A renderer or adapter then converts that operation into the representation required by a concrete runtime.

This prevents command handlers from containing shell quoting, Python syntax generation, or transport details.

## Renderer Responsibilities

A renderer may be responsible for:

- encoding operation arguments;
- applying runtime-specific syntax;
- producing a payload;
- selecting the correct channel or delivery path.

It should not silently change the operation's meaning.

## Validation Before Rendering

Operations should be validated before rendering:

- required arguments exist;
- values have the expected type;
- paths satisfy boundary rules;
- mutually exclusive options are rejected;
- the operation is supported by the selected runtime.

Rendering invalid input can produce ambiguous or unsafe payloads.

## Unknown Operations

A receiver must define behavior for an unknown operation code:

- reject it;
- return a structured unsupported-operation error;
- ignore it only when the protocol explicitly allows that behavior.

Guessing an operation from payload text defeats the purpose of explicit codes.

## Verification Strategy

Test:

1. one operation per code;
2. renderer output for each supported runtime;
3. invalid argument rejection;
4. unsupported operation handling;
5. operation ordering;
6. round-trip interpretation;
7. separation between handlers and renderers.

## Conclusion

Operation codes provide a stable vocabulary between intent and execution. A renderer can adapt that vocabulary to different runtimes while keeping command logic independent of transport syntax.

The central design rule is:

> Represent intent once; adapt its encoding at the runtime boundary.
