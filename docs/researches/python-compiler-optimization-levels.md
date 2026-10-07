# Python Compiler Optimization Levels

## Central Question

What transformations does Python apply when source code is compiled with different optimization levels?

## Scope

This research covers only:

- the `optimize` parameter of `compile`;
- optimization levels `0`, `1`, and `2`;
- removal of assertions;
- removal of docstrings;
- observable effects in generated code objects.

It does not cover AST transformations, tokenization, bytecode serialization, network transport, or source minification.

## Optimization Levels

Python exposes three commonly used optimization levels:

| Level | Equivalent flag | Main behavior                        |
| :---: | :-------------: | :----------------------------------- |
|  `0`  |      none       | Preserves assertions and docstrings. |
|  `1`  |      `-O`       | Removes assertions.                  |
|  `2`  |      `-OO`      | Removes assertions and docstrings.   |

The level is passed to `compile`:

```python
code = compile(
    source,
    "<input>",
    "exec",
    optimize=2,
)
```

## Level 0

At level `0`, assertions remain executable:

```python
source = """
assert False, "validation failed"
"""

code = compile(source, "<input>", "exec", optimize=0)
```

Executing the resulting code raises `AssertionError`.

Docstrings also remain available:

```python
source = '''
def greet():
    """Function documentation."""
    return "hello"
'''

namespace: dict[str, object] = {}
exec(compile(source, "<input>", "exec", optimize=0), namespace)

assert namespace["greet"].__doc__ == "Function documentation."
```

## Level 1

At level `1`, assertion statements are removed during compilation:

```python
source = """
assert False, "this is removed"
result = 42
"""

namespace: dict[str, object] = {}
exec(compile(source, "<input>", "exec", optimize=1), namespace)

assert namespace["result"] == 42
```

The assertion condition is not evaluated:

```python
source = """
def side_effect():
    raise RuntimeError("should not run")

assert side_effect()
"""

namespace: dict[str, object] = {}
exec(compile(source, "<input>", "exec", optimize=1), namespace)
```

The function definition succeeds because the assertion expression is omitted from the compiled code.

This means optimization level `1` is not behaviorally equivalent to simply hiding assertion failures. It removes the complete assertion statement, including evaluation of its condition and message.

## Level 2

At level `2`, assertions and docstrings are removed:

```python
source = '''
def greet():
    """Function documentation."""
    assert True
    return "hello"
'''

namespace: dict[str, object] = {}
exec(compile(source, "<input>", "exec", optimize=2), namespace)

greet = namespace["greet"]
assert greet() == "hello"
assert greet.__doc__ is None
```

Level `2` changes the function's `__doc__` value. Code that relies on runtime documentation must not use this level indiscriminately.

## What Optimization Does Not Remove

The compiler optimization level does not generally remove:

- comments from the source text;
- type annotations;
- arbitrary string literals;
- unused variables;
- unreachable code in the general case;
- function calls with possible side effects;
- imports;
- debugging metadata in the same way as a source transformer.

For example, annotations remain visible:

```python
source = """
def add(left: int, right: int) -> int:
    return left + right
"""

namespace: dict[str, object] = {}
exec(compile(source, "<input>", "exec", optimize=2), namespace)

assert namespace["add"].__annotations__ == {
    "left": int,
    "right": int,
    "return": int,
}
```

Optimization levels should therefore not be confused with source sanitization or general-purpose minification.

## Runtime Expressions in Docstrings

A conventional docstring is a string literal in the first position of a body:

```python
def run():
    """Documentation."""
```

At optimization level `2`, the compiler removes its runtime documentation value.

Other string expressions should not be assumed to be removable:

```python
def run():
    value = "runtime data"
    return value
```

The string assigned to `value` remains necessary for execution.

## Inspecting the Result

The effect of optimization can be inspected through code object metadata:

```python
source = '''
"""Module documentation."""

def run():
    """Function documentation."""
    assert True
    return 1
'''

for level in (0, 1, 2):
    code = compile(source, "<input>", "exec", optimize=level)

    print(level, code.co_consts)
```

A useful comparison should inspect:

- `co_consts`;
- function `__doc__`;
- whether assertions execute;
- whether assertion messages remain;
- the final execution result.

Disassembly can also reveal whether assertion instructions remain:

```python
import dis

code = compile(
    "assert value > 0\n",
    "<input>",
    "exec",
    optimize=2,
)

dis.dis(code)
```

## Semantic Risks

Optimization is unsafe when assertions are part of the application contract:

```python
assert validate_state()
```

The call to `validate_state()` disappears at optimization levels `1` and `2`.

It is also unsafe when runtime documentation is required:

```python
handler.__doc__
```

At level `2`, this may return `None`.

Optimization is appropriate only when the program treats assertions as development checks and does not depend on docstrings at runtime.

## Verification Strategy

A test suite should verify each level independently:

1. Level `0` preserves assertions.
2. Level `0` preserves docstrings.
3. Level `1` removes assertions.
4. Level `1` preserves docstrings.
5. Level `2` removes assertions.
6. Level `2` removes docstrings.
7. Assertion expressions are not evaluated at levels `1` and `2`.
8. Ordinary string literals remain.
9. Type annotations are not assumed to be removed.
10. The resulting code object remains executable.

Example:

```python
source = '''
def calculate(value: int) -> int:
    """Calculate a value."""
    assert value >= 0
    return value + 1
'''

for level in (0, 1, 2):
    namespace: dict[str, object] = {}
    code = compile(source, "<input>", "exec", optimize=level)
    exec(code, namespace)

    function = namespace["calculate"]

    if level == 0:
        assert function.__doc__ == "Calculate a value."
    elif level == 1:
        assert function.__doc__ == "Calculate a value."
    else:
        assert function.__doc__ is None
```

## Limitations

Compiler optimization levels are:

- implementation behavior, not a source-code rewriting policy;
- not a security mechanism;
- not a sandbox;
- not a substitute for static analysis;
- not a complete minifier;
- not a guarantee of semantic equivalence.

The exact generated bytecode may vary between Python implementations and versions.

## Conclusion

The `optimize` parameter provides a narrowly defined compiler-level transformation:

- level `1` removes assertions;
- level `2` additionally removes docstrings.

It should be selected according to runtime requirements, not simply because a higher number appears to produce a smaller result.

The central design rule is:

> Compiler optimization removes specific runtime structures; it does not understand the full intent of the program.
