# Python In-Memory Execution

## Central Question

What does it mean to compile and execute Python code in memory, and which resources remain involved despite avoiding a source file?

## Scope

This research covers the `compile` and `exec` model, persistent namespaces, output streams, exceptions, and the distinction between avoiding a source file and providing isolation.

It does not cover AST sanitization, compiler optimization levels, bytecode serialization, transport framing, or sandbox design.

## Execution Model

Python source can be compiled into a code object and executed from a namespace:

```python
source = "value = 40 + 2"
code = compile(source, "<memory>", "exec")
namespace: dict[str, object] = {}
exec(code, namespace)

assert namespace["value"] == 42
```

The source does not need to be saved as a `.py` file before execution.

## Persistent Namespace

Repeated executions can share state when they use the same namespace:

```python
namespace: dict[str, object] = {}
exec("value = 41", namespace)
exec("result = value + 1", namespace)

assert namespace["result"] == 42
```

This persistence is useful for sessions, but it also means that one execution can affect later executions through variables, imports, functions, and modified objects.

A fresh namespace provides a new Python global scope, but it does not isolate the process itself.

## Output and Errors

Execution writes to the process's configured output and error streams unless they are explicitly redirected:

```python
import contextlib
import io

output = io.StringIO()
with contextlib.redirect_stdout(output):
    exec("print('hello')", {})

assert output.getvalue() == "hello\n"
```

Output capture is a routing mechanism. It is not a security boundary.

Exceptions remain part of normal execution and should be reported separately from captured output.

## Process Resources

In-memory execution can still:

- import modules;
- open files;
- create subprocesses;
- access network resources;
- modify environment variables;
- allocate memory;
- terminate the process.

Avoiding a source file changes storage and delivery, not the privileges of the interpreter process.

## Lifecycle

A session should define:

- when the namespace is created;
- whether state persists between executions;
- how exceptions affect later executions;
- how output streams are restored;
- when resources are released;
- whether a session can be reset.

A failed execution may leave partially initialized state behind. A reset policy is therefore required for predictable sessions.

## Verification Strategy

Test at least:

1. simple assignment and expression execution;
2. state shared across executions;
3. state reset with a new namespace;
4. stdout capture and restoration;
5. stderr handling;
6. exception reporting;
7. imports and cleanup;
8. behavior after partial failure;
9. attempts to access process resources.

## Conclusion

In-memory Python execution means that source or compiled code is delivered directly to an interpreter without first creating a source file. It does not imply process isolation, filesystem isolation, privilege reduction, or safe execution of untrusted code.

The central design rule is:

> In-memory describes where code is delivered, not what the interpreter is allowed to do.
