import ast
import importlib.util
import marshal
import platform
import sys
import types

__all__ = [
    "NativeSourceSanitizer",
    "check_bytecode_compatibility",
    "compile_and_serialize",
    "compile_source",
    "sanitize_source",
    "serialize_code",
]


class NativeSourceSanitizer(ast.NodeTransformer):
    """Prunes comments, docstrings, type annotations, and asserts from Python AST."""

    def __init__(
        self,
        *,
        strip_docstrings: bool = True,
        strip_annotations: bool = True,
        strip_asserts: bool = True,
    ) -> None:
        super().__init__()

        self.strip_docstrings = strip_docstrings
        self.strip_annotations = strip_annotations
        self.strip_asserts = strip_asserts

    def _strip_docstring(self, body: list[ast.stmt]) -> None:
        """Remove docstring node if present as the first statement in a body."""

        if (
            self.strip_docstrings
            and body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            body.pop(0)

    def visit_Module(self, node: ast.Module) -> ast.Module:
        """Visit module node and strip top-level docstring."""

        self.generic_visit(node)
        self._strip_docstring(node.body)

        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Visit function definition and strip docstring and type annotations."""

        self.generic_visit(node)
        self._strip_docstring(node.body)

        if self.strip_annotations:
            node.returns = None

            for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                arg.annotation = None

            if node.args.vararg:
                node.args.vararg.annotation = None

            if node.args.kwarg:
                node.args.kwarg.annotation = None

        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """Visit async function definition and strip docstring and type annotations."""

        self.generic_visit(node)
        self._strip_docstring(node.body)

        if self.strip_annotations:
            node.returns = None

            for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                arg.annotation = None

            if node.args.vararg:
                node.args.vararg.annotation = None

            if node.args.kwarg:
                node.args.kwarg.annotation = None

        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Visit class definition and strip docstring."""

        self.generic_visit(node)
        self._strip_docstring(node.body)

        return node

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST | None:
        """Convert typed variable declaration `x: int = 1` into simple `x = 1`."""

        if not self.strip_annotations:
            return node

        if node.value is None:
            return None

        return ast.Assign(targets=[node.target], value=node.value)

    def visit_Assert(self, node: ast.Assert) -> ast.AST | None:
        """Strip development assertion statements if enabled."""

        if self.strip_asserts:
            return None

        return node


def sanitize_source(
    source: str,
    *,
    strip_docstrings: bool = True,
    strip_annotations: bool = True,
    strip_asserts: bool = True,
) -> str:
    """Sanitize Python source by removing comments, docstrings, annotations, and asserts.

    Args:
        source: Raw Python source code string.
        strip_docstrings: Whether to strip module, class, and function docstrings.
        strip_annotations: Whether to remove parameter, return, and variable type hints.
        strip_asserts: Whether to eliminate assertion statements.

    Returns:
        Cleaned, syntactically valid Python source code string.
    """

    tree = ast.parse(source)
    sanitizer = NativeSourceSanitizer(
        strip_docstrings=strip_docstrings,
        strip_annotations=strip_annotations,
        strip_asserts=strip_asserts,
    )

    cleaned_tree = sanitizer.visit(tree)
    ast.fix_missing_locations(cleaned_tree)

    return ast.unparse(cleaned_tree)


def compile_source(
    source: str,
    filename: str = "<remote>",
    optimize: int = 2,
) -> types.CodeType:
    """Compile Python source code into an executable code object.

    Args:
        source: Python source code string.
        filename: Diagnostic filename metadata included in stack traces.
        optimize: Compiler optimization level (default 2 removes asserts and docstrings).

    Returns:
        Compiled executable CodeType object.

    Raises:
        SyntaxError: If source contains invalid Python syntax.
    """

    return compile(source, filename, "exec", optimize=optimize)


def serialize_code(code: types.CodeType) -> bytes:
    """Serialize a Python code object into bytes using CPython marshal.

    Args:
        code: Compiled code object.

    Returns:
        Marshaled bytecode payload.
    """

    return marshal.dumps(code)


def compile_and_serialize(
    source: str,
    filename: str = "<remote>",
    optimize: int = 2,
    *,
    sanitize: bool = False,
) -> bytes:
    """Compile Python source and serialize the resulting code object to bytes.

    Args:
        source: Python source code string.
        filename: Diagnostic filename metadata.
        optimize: Compiler optimization level (default 2).
        sanitize: Whether to run AST-level source sanitization before compiling.

    Returns:
        Marshaled bytecode payload ready for network transport.
    """

    code_source = sanitize_source(source) if sanitize else source
    code = compile_source(code_source, filename, optimize=optimize)

    return serialize_code(code)


def check_bytecode_compatibility(
    client_magic: bytes | str,
    client_version: tuple[int, ...] | list[int],
    client_implementation: str = "CPython",
) -> bool:
    """Evaluate whether client and host share compatible Python bytecode formats.

    Bytecode compatibility requires matching Python implementations (e.g. CPython),
    identical CPython bytecode magic numbers (importlib.util.MAGIC_NUMBER), and
    matching major and minor Python version numbers.

    Args:
        client_magic: Client bytecode magic number as bytes or hex string.
        client_version: Client Python version tuple or list (e.g. [3, 13, 1]).
        client_implementation: Python implementation string (default 'CPython').

    Returns:
        True if bytecode compiled on the host can safely execute on client.
    """

    if client_implementation != platform.python_implementation():
        return False

    if isinstance(client_magic, str):
        try:
            magic_bytes = bytes.fromhex(client_magic)
        except ValueError:
            return False
    else:
        magic_bytes = client_magic

    if magic_bytes != importlib.util.MAGIC_NUMBER:
        return False

    if len(client_version) < 2:
        return False

    return tuple(client_version[:2]) == sys.version_info[:2]
