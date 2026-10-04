import importlib.util
import platform
import sys
import types

import pytest

from declusor import lang


class TestCompileSource:
    """Tests for lang.python compile_source function."""

    def test_compile_source__valid_python__returns_code_type(self) -> None:
        """Verify compile_source compiles Python text into an executable CodeType."""

        code = lang.python.compile_source("result = 1 + 2\n")

        assert isinstance(code, types.CodeType)

        scope: dict[str, object] = {}
        exec(code, scope)
        assert scope["result"] == 3

    def test_compile_source__default_optimize_2__strips_docstrings_and_asserts(self) -> None:
        """Verify default optimize=2 removes docstrings and assertions from bytecode constants."""

        source = '"""Module docstring."""\ndef foo():\n    """Function docstring."""\n    assert 1 > 0, "assertion message"\n    return 42\n'
        code = lang.python.compile_source(source)

        assert "Module docstring." not in code.co_consts
        assert "assertion message" not in code.co_consts

        scope: dict[str, object] = {}
        exec(code, scope)
        assert scope["foo"]() == 42  # type: ignore[operator]

    def test_compile_source__custom_optimize_0__preserves_docstrings(self) -> None:
        """Verify optimize=0 preserves docstrings in bytecode constants."""

        source = '"""Module docstring."""\nx = 1\n'
        code = lang.python.compile_source(source, optimize=0)

        assert "Module docstring." in code.co_consts

    def test_compile_source__custom_filename__sets_co_filename(self) -> None:
        """Verify compile_source embeds the specified filename for tracebacks."""

        code = lang.python.compile_source("x = 42\n", filename="<custom_test>")

        assert code.co_filename == "<custom_test>"

    def test_compile_source__syntax_error__raises_syntax_error(self) -> None:
        """Verify compile_source raises SyntaxError when code has invalid syntax."""

        with pytest.raises(SyntaxError):
            lang.python.compile_source("def broken(\n")


class TestSanitizeSource:
    """Tests for lang.python sanitize_source AST pruning."""

    def test_sanitize_source__comments_and_docstrings__strips_all(self) -> None:
        """Verify sanitize_source strips comments and docstrings while preserving logic."""

        source = (
            "# Top level comment\n"
            '"""Module docstring."""\n'
            "def compute(a: int, b: int = 10) -> int:\n"
            '    """Compute sum of values."""\n'
            "    # Inline calculation\n"
            "    return a + b\n"
        )
        cleaned = lang.python.sanitize_source(source)

        assert "# Top level comment" not in cleaned
        assert "Module docstring." not in cleaned
        assert "Compute sum of values." not in cleaned
        assert "# Inline calculation" not in cleaned

        scope: dict[str, object] = {}
        exec(cleaned, scope)
        assert scope["compute"](5) == 15  # type: ignore[operator]

    def test_sanitize_source__type_annotations__strips_hints_and_ann_assign(self) -> None:
        """Verify sanitize_source removes parameter hints, return hints, and variable annotations."""

        source = "x: int = 100\ny: str\ndef greet(name: str) -> str:\n    return 'Hello ' + name\n"
        cleaned = lang.python.sanitize_source(source)

        assert ": int" not in cleaned
        assert ": str" not in cleaned
        assert "-> str" not in cleaned

        scope: dict[str, object] = {}
        exec(cleaned, scope)
        assert scope["x"] == 100
        assert scope["greet"]("World") == "Hello World"  # type: ignore[operator]

    def test_sanitize_source__assertions__strips_assert_statements(self) -> None:
        """Verify sanitize_source eliminates assert statements from cleaned code."""

        source = 'def check_positive(n):\n    assert n > 0, "Must be positive"\n    return n * 2\n'
        cleaned = lang.python.sanitize_source(source)

        assert "assert" not in cleaned
        assert "Must be positive" not in cleaned

        scope: dict[str, object] = {}
        exec(cleaned, scope)
        assert scope["check_positive"](-5) == -10  # type: ignore[operator]

    def test_sanitize_source__async_functions_and_classes__strips_docstrings(self) -> None:
        """Verify sanitize_source strips docstrings from classes and async functions."""

        source = (
            "class MyService:\n"
            '    """Class docstring."""\n'
            "    def method(self):\n"
            '        """Method docstring."""\n'
            "        return True\n"
            "\n"
            "async def async_worker(timeout: float = 1.0) -> None:\n"
            '    """Async docstring."""\n'
            "    pass\n"
        )
        cleaned = lang.python.sanitize_source(source)

        assert "Class docstring." not in cleaned
        assert "Method docstring." not in cleaned
        assert "Async docstring." not in cleaned
        assert ": float" not in cleaned
        assert "-> None" not in cleaned


class TestSerialization:
    """Tests for lang.python serialization utilities."""

    def test_serialize_code__valid_code__returns_bytes(self) -> None:
        """Verify serialize_code returns marshaled bytes for a code object."""

        code = lang.python.compile_source("value = 100\n")
        payload = lang.python.serialize_code(code)

        assert isinstance(payload, bytes)
        assert len(payload) > 0

    def test_compile_and_serialize__valid_source__returns_serialized_bytes(self) -> None:
        """Verify compile_and_serialize produces identical payload to serialize_code."""

        source = "msg = 'declusor_ok'\n"
        payload = lang.python.compile_and_serialize(source, filename="<pipe>")
        expected = lang.python.serialize_code(lang.python.compile_source(source, filename="<pipe>"))

        assert payload == expected

    def test_compile_and_serialize__with_sanitize_true__compiles_sanitized_source(self) -> None:
        """Verify compile_and_serialize with sanitize=True compiles sanitized AST source."""

        source = '# Development comment\ndef multiply(a: int, b: int) -> int:\n    """Docstring."""\n    return a * b\nres = multiply(6, 7)\n'
        payload = lang.python.compile_and_serialize(source, sanitize=True)
        sanitized = lang.python.sanitize_source(source)
        expected = lang.python.serialize_code(lang.python.compile_source(sanitized, "<remote>"))

        assert payload == expected


class TestBytecodeCompatibility:
    """Tests for lang.python check_bytecode_compatibility function."""

    def test_check_bytecode_compatibility__matching_magic_and_version__returns_true(self) -> None:
        """Verify check_bytecode_compatibility returns True when magic and version match host."""

        magic = importlib.util.MAGIC_NUMBER
        version = list(sys.version_info[:3])

        compatible = lang.python.check_bytecode_compatibility(magic, version, platform.python_implementation())
        assert compatible is True

    def test_check_bytecode_compatibility__matching_hex_magic_and_version__returns_true(self) -> None:
        """Verify check_bytecode_compatibility accepts hex string magic numbers."""

        magic_hex = importlib.util.MAGIC_NUMBER.hex()
        version = tuple(sys.version_info[:2])

        compatible = lang.python.check_bytecode_compatibility(magic_hex, version)
        assert compatible is True

    def test_check_bytecode_compatibility__different_magic__returns_false(self) -> None:
        """Verify check_bytecode_compatibility returns False when magic number differs."""

        mismatched_magic = b"\x00\x00\x00\x00"

        compatible = lang.python.check_bytecode_compatibility(mismatched_magic, list(sys.version_info[:3]))
        assert compatible is False

    def test_check_bytecode_compatibility__different_version__returns_false(self) -> None:
        """Verify check_bytecode_compatibility returns False when minor version differs."""

        magic = importlib.util.MAGIC_NUMBER
        different_version = (sys.version_info.major, sys.version_info.minor + 1, 0)

        compatible = lang.python.check_bytecode_compatibility(magic, different_version)
        assert compatible is False

    def test_check_bytecode_compatibility__different_implementation__returns_false(self) -> None:
        """Verify check_bytecode_compatibility returns False for non-matching implementation."""

        magic = importlib.util.MAGIC_NUMBER
        version = list(sys.version_info[:3])

        compatible = lang.python.check_bytecode_compatibility(magic, version, client_implementation="PyPy")
        assert compatible is False

    def test_check_bytecode_compatibility__invalid_hex_string__returns_false(self) -> None:
        """Verify check_bytecode_compatibility returns False when hex string is invalid."""

        compatible = lang.python.check_bytecode_compatibility("invalid_hex!", list(sys.version_info[:3]))
        assert compatible is False

    def test_check_bytecode_compatibility__version_too_short__returns_false(self) -> None:
        """Verify check_bytecode_compatibility returns False when version has fewer than 2 elements."""

        magic = importlib.util.MAGIC_NUMBER

        compatible = lang.python.check_bytecode_compatibility(magic, [3])
        assert compatible is False
