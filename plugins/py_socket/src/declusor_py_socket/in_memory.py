"""Python in-memory compilation, serialization, and runtime compatibility utilities.

Provides utilities for compiling Python source code to bytecode code objects,
serializing and deserializing them via marshal, and evaluating CPython runtime
bytecode compatibility between host and client agents.
"""

import importlib.util
import marshal
import platform
import sys
import types


def compile_source(source: str, filename: str = "<remote>") -> types.CodeType:
    """Compile Python source code into an executable code object.

    Args:
        source: Python source code string.
        filename: Diagnostic filename metadata included in stack traces.

    Returns:
        Compiled executable CodeType object.

    Raises:
        SyntaxError: If source contains invalid Python syntax.
    """

    return compile(source, filename, "exec")


def serialize_code(code: types.CodeType) -> bytes:
    """Serialize a Python code object into bytes using CPython marshal.

    Args:
        code: Compiled code object.

    Returns:
        Marshaled bytecode payload.
    """

    return marshal.dumps(code)


def deserialize_code(payload: bytes) -> types.CodeType:
    """Deserialize raw bytes into a Python code object using CPython marshal.

    Args:
        payload: Marshaled bytecode bytes.

    Returns:
        Deserialized CodeType object.

    Raises:
        ValueError: If payload is corrupted or does not represent a code object.
    """

    try:
        obj = marshal.loads(payload)
    except Exception as exc:
        raise ValueError(f"Failed to deserialize marshaled code: {exc}") from exc

    if not isinstance(obj, types.CodeType):
        raise ValueError(f"Deserialized object is {type(obj).__name__}, expected CodeType.")

    return obj


def compile_and_serialize(source: str, filename: str = "<remote>") -> bytes:
    """Compile Python source and serialize the resulting code object to bytes.

    Args:
        source: Python source code string.
        filename: Diagnostic filename metadata.

    Returns:
        Marshaled bytecode payload ready for network transport.
    """

    code = compile_source(source, filename)

    return serialize_code(code)


def can_deserialize_code(payload: bytes) -> bool:
    """Check whether a byte sequence represents a valid marshaled CodeType object.

    Args:
        payload: Byte sequence to validate.

    Returns:
        True if payload successfully unpacks to a CodeType, False otherwise.
    """

    try:
        obj = marshal.loads(payload)
        return isinstance(obj, types.CodeType)
    except Exception:
        return False


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
