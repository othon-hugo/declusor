# AST-Based Source Sanitization

## Central Question

How can Python source code be structurally reduced with the standard-library AST while preserving the executable behavior that matters?

## Scope

This research covers:

- parsing source code with `ast.parse`;
- transforming syntax trees with `ast.NodeTransformer`;
- removing comments, docstrings, annotations, and assertions;
- reconstructing source with `ast.unparse`;
- identifying semantic changes caused by the transformation.

It does not cover tokenization, compiler optimization, bytecode serialization, network transport, or sandboxing.

## Hypothesis

AST-based sanitization can remove selected non-essential syntax from controlled Python programs without external dependencies. However, the transformation is not generally semantics-preserving because annotations and assertions may contain executable expressions.

## Comments

Comments are not represented as ordinary nodes in Python's AST. When the transformed tree is reconstructed, comments are therefore not emitted:

```python
# This comment is discarded
value = 42
```

The resulting source contains the assignment but not the comment.

This behavior is different from removing string literals. A string is part of the AST and may represent executable data, even when it visually resembles documentation.

## Docstrings

A docstring is a string expression in the first position of a module, class, or function body:

```python
def greet() -> None:
    """Describe the function."""
    print("hello")
```

A sanitizer can identify this specific position and remove it without removing other string expressions.

The following string is not a docstring:

```python
def greet() -> None:
    message = "hello"
    print(message)
```

Removing arbitrary string expressions would risk changing program behavior.

## Function Annotations

Function annotations can be removed from parameters and return values:

```python
def add(left: int, right: int) -> int:
    return left + right
```

After sanitization:

```python
def add(left, right):
    return left + right
```

This is only behavior-neutral when annotations are not needed at runtime.

Annotations may contain executable expressions:

```python
def process(value: register_type()) -> None:
    return None
```

Removing the annotation also removes the call to `register_type()`. Therefore, annotations must be treated as syntax that may have runtime effects, not as universally inert metadata.

## Variable Annotations

An annotated assignment with a value can be reduced:

```python
count: int = 10
```

to:

```python
count = 10
```

An annotation without a value:

```python
count: int
```

can be removed when the annotation itself is not required by the program.

This transformation may still be unsafe when the annotation expression has side effects:

```python
count: register_type()
```

## Assertions

Assertions can be removed:

```python
assert value > 0, "value must be positive"
```

After sanitization, the validation and its message disappear completely.

This changes behavior whenever the assertion is part of the program's runtime validation:

```python
assert initialize_state()
```

Removing it also removes the call to `initialize_state()`.

Assertions should therefore be classified as development checks only when the input program guarantees that they do not provide required runtime behavior.

## Minimal Transformer

A minimal implementation can use `ast.NodeTransformer`:

```python
import ast


class Sanitizer(ast.NodeTransformer):
    def _remove_docstring(self, body: list[ast.stmt]) -> None:
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
            body.pop(0)

    def visit_Module(self, node: ast.Module) -> ast.Module:
        self.generic_visit(node)
        self._remove_docstring(node.body)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        self.generic_visit(node)
        self._remove_docstring(node.body)
        node.returns = None

        for argument in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
            argument.annotation = None

        if node.args.vararg is not None:
            node.args.vararg.annotation = None

        if node.args.kwarg is not None:
            node.args.kwarg.annotation = None

        return node

    def visit_Assert(self, node: ast.Assert) -> ast.AST | None:
        return None
```

After transformation, missing source locations should be restored:

```python
tree = ast.parse(source)
tree = Sanitizer().visit(tree)
ast.fix_missing_locations(tree)
result = ast.unparse(tree)
```

## Important AST Rules

A transformer must:

- call `generic_visit` when child nodes also need transformation;
- return `None` only when a node should be removed;
- preserve nodes that are outside the intended policy;
- call `ast.fix_missing_locations` before compilation or unparsing;
- distinguish docstrings from ordinary string expressions;
- make removal policies explicit and configurable.

## Verification Strategy

A sanitizer should be tested with small independent examples:

1. Comments disappear.
2. Module, class, and function docstrings disappear.
3. Function annotations disappear.
4. Annotated assignments retain their values.
5. Assertions disappear.
6. Ordinary string literals remain.
7. The transformed source still parses.
8. A representative program retains its expected result.
9. Annotation and assertion side effects are intentionally tested as behavior changes.

Example:

```python
source = """
def calculate(value: int) -> int:
    \"\"\"Calculate a result.\"\"\"
    assert value >= 0
    return value + 1
"""

tree = ast.parse(source)
cleaned_tree = Sanitizer().visit(tree)
ast.fix_missing_locations(cleaned_tree)
cleaned = ast.unparse(cleaned_tree)

compile(cleaned, "<sanitized>", "exec")
assert "Calculate a result" not in cleaned
assert "assert" not in cleaned
assert ": int" not in cleaned
```

## Limitations

AST sanitization is not:

- a general-purpose minifier;
- a semantic-equivalence proof;
- a security boundary;
- a sandbox;
- a substitute for static analysis;
- a guarantee that the resulting program behaves identically.

The transformation is safest when applied to controlled source code with a documented policy describing which syntax is disposable.

## Conclusion

AST-based sanitization is useful when a program must be structurally reduced without external dependencies. Its reliability comes from targeting specific syntax nodes rather than manipulating source text with regular expressions.

The central design rule is:

> Remove only syntax whose runtime significance has been explicitly evaluated.

Comments and conventional docstrings are usually safe candidates. Annotations and assertions require more caution because their expressions may execute code.
