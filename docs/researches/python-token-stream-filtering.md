# Token-Based Source Filtering

## Central Question

When is token-level filtering appropriate for reducing Python source code, and what syntax cannot be safely transformed without an AST?

## Scope

This research covers:

- tokenization with Python's `tokenize` module;
- removal of comments;
- preservation of valid spacing and indentation;
- identification of string tokens;
- limitations of detecting docstrings lexically;
- reconstruction with `tokenize.untokenize`.

It does not cover AST transformations, compiler optimization, bytecode serialization, transport protocols, or semantic analysis.

## Hypothesis

Token-level filtering is useful for transformations that depend only on lexical information, such as removing comments. It becomes unreliable when a transformation depends on syntactic context, such as distinguishing docstrings from ordinary string literals.

## Tokenization

Python source can be converted into a sequence of tokens:

```python
import io
import tokenize

source = "value = 1  # comment\n"

tokens = tokenize.generate_tokens(io.StringIO(source).readline)

for token in tokens:
    print(token.type, repr(token.string))
```

Tokens retain information such as:

- token type;
- token text;
- start position;
- end position;
- source line.

This makes tokenization more structured than regular-expression replacement while remaining lighter than constructing an AST.

## Removing Comments

Comments have their own token type:

```python
import io
import tokenize


def remove_comments(source: str) -> str:
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)

    filtered = (token for token in tokens if token.type != tokenize.COMMENT)

    return tokenize.untokenize(filtered)
```

This removes comments without accidentally deleting a `#` character inside a string:

```python
value = "# this is data"
# this is a comment
```

The string remains intact because its contents are represented by a `STRING` token.

## Whitespace and Reconstruction

Token filtering must preserve enough layout information for the result to remain valid Python.

Important token types include:

- `INDENT`;
- `DEDENT`;
- `NEWLINE`;
- `NL`;
- `INDENT`;
- `COMMENT`;
- `ENCODING`;
- `ENDMARKER`.

`tokenize.untokenize` reconstructs source from token data, but formatting may change. The result should be treated as equivalent source, not as a byte-for-byte rewrite.

A transformation that removes tokens must verify that it does not remove structural tokens required for indentation or statement boundaries.

## Why Docstrings Are Different

A docstring is represented lexically as a `STRING` token. The token itself does not identify whether it is:

- a module docstring;
- a class docstring;
- a function docstring;
- an ordinary string expression;
- a string assigned to a variable;
- part of a larger expression.

For example:

```python
"""module documentation"""

value = "ordinary data"


def run() -> None:
    """function documentation"""
    message = "ordinary data"
    return None
```

The documentation strings and ordinary strings all appear as string tokens. Determining their meaning requires context such as:

- whether the token is the first statement in a body;
- indentation level;
- preceding structural tokens;
- whether it belongs to a module, class, or function suite.

A simple rule such as “remove every string after `INDENT`” is unsafe.

## Example of an Unsafe Filter

This filter is not a reliable docstring remover:

```python
if token.type == tokenize.STRING:
    continue
```

It can remove runtime data:

```python
message = "keep this value"
print(message)
```

It can also break expressions:

```python
items = [
    "first",
    "second",
]
```

Token-level processing should remove only syntax whose lexical meaning is unambiguous.

## Type Comments

Type comments are represented differently from regular comments depending on the parsing configuration and Python version.

A filter that removes all `COMMENT` tokens may remove type comments such as:

```python
value = 1  # type: int
```

This may be desirable for payload reduction, but it must be an explicit policy. Removing comments should not silently imply that all type information is disposable.

## Strings and Escaping

Token-based filtering preserves the original string token text, including quoting and escaping:

```python
value = "text containing # and \\"quotes\\""
```

This is safer than searching the raw source for comment markers, because `#` inside a string is not treated as a comment.

Any transformation that rewrites string tokens must account for:

- single and double quotes;
- triple-quoted strings;
- raw strings;
- bytes literals;
- f-strings;
- escape sequences;
- implicit concatenation.

## Syntax Validation

A token filter should validate its output:

```python
import ast

filtered_source = remove_comments(source)
ast.parse(filtered_source)
```

Successful tokenization does not guarantee that the transformed source is syntactically valid. Removing tokens can alter statement boundaries or indentation relationships.

Validation should occur before the result is compiled or executed.

## Verification Strategy

A minimal test set should verify:

1. Comments are removed.
2. `#` inside strings is preserved.
3. Indentation remains valid.
4. Blank-line behavior is acceptable.
5. Strings used as data remain unchanged.
6. Type comments are either preserved or intentionally removed.
7. Multiline strings remain valid.
8. F-strings remain valid.
9. The reconstructed result can be parsed.
10. Representative behavior is preserved.

Example:

```python
source = """
# remove this
message = "# preserve this value"

def display() -> None:
    # remove this too
    return message
"""

filtered = remove_comments(source)
compile(filtered, "<filtered>", "exec")

scope: dict[str, object] = {}
exec(filtered, scope)

assert scope["display"]() == "# preserve this value"
```

## Strengths

Token-level filtering is appropriate when:

- the transformation is lexical;
- source formatting should mostly be retained;
- comments are the only target;
- AST construction would be unnecessary overhead;
- the output must preserve original token text.

## Limitations

Tokenization alone does not reliably provide:

- semantic information;
- scope information;
- declaration context;
- a safe distinction between docstrings and ordinary strings;
- symbol analysis;
- equivalence guarantees.

It should not be used as a replacement for AST processing when the transformation depends on program structure.

## Decision Rule

Use tokenization for lexical transformations.

Use an AST when the transformation depends on syntax-tree context.

Use semantic analysis when correctness depends on names, scopes, types, or runtime effects.

## Conclusion

Token-level filtering occupies a useful middle ground between raw text manipulation and full AST transformation. It is precise enough to remove comments without corrupting string literals, but it cannot safely infer the meaning of every token.

The central design rule is:

> A token can reveal what text is present, but not always what role that text plays in the program.
