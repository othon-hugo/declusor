# Language Utilities Package

The **util.lang** package provides language-specific compilation, code pruning, AST transformation, and runtime execution helpers consumed across transport plugins and execution pipelines.

> [!NOTE]
> Depends only on Python standard library and `config` — zero circular dependencies.

## Modules

| Module   | Responsibility                                                                                                 |
| -------- | -------------------------------------------------------------------------------------------------------------- |
| `python` | Python in-memory compilation, AST-level source sanitization, bytecode serialization, and runtime compatibility |

## Design Principles

1. **Zero External Dependencies** — strictly utilizes standard library modules (`ast`, `compile`, `marshal`) without heavy third-party minification or data-analysis frameworks.
2. **Stateless Purity** — all functions are pure, deterministic, or defensive.
3. **Dual-Mode Optimization** — supports native CPython compiler optimization (`optimize=2`) for homogeneous bytecode execution and AST pruning (`ast.unparse`) for cross-version portable source execution.
4. **Static Type Checking** — functions and classes are checked by the repository's configured Mypy strict profile.
