import importlib.util
import marshal
import platform
import sys
import types

import declusor_py_socket as py_socket
import pytest


class TestCompileSource:
    """Tests for in_memory compile_source function."""

    def test_compile_source__valid_python__returns_code_type(self) -> None:
        """Verify compile_source compiles Python text into an executable CodeType."""

        code = py_socket.compile_source("result = 1 + 2\n")

        assert isinstance(code, types.CodeType)

        scope: dict[str, object] = {}
        exec(code, scope)
        assert scope["result"] == 3

    def test_compile_source__custom_filename__sets_co_filename(self) -> None:
        """Verify compile_source embeds the specified filename for tracebacks."""

        code = py_socket.compile_source("x = 42\n", filename="<custom_test>")

        assert code.co_filename == "<custom_test>"

    def test_compile_source__syntax_error__raises_syntax_error(self) -> None:
        """Verify compile_source raises SyntaxError when code has invalid syntax."""

        with pytest.raises(SyntaxError):
            py_socket.compile_source("def broken(\n")


class TestSerialization:
    """Tests for in_memory serialization and deserialization utilities."""

    def test_serialize_code__valid_code__returns_bytes(self) -> None:
        """Verify serialize_code returns marshaled bytes for a code object."""

        code = py_socket.compile_source("value = 100\n")
        payload = py_socket.serialize_code(code)

        assert isinstance(payload, bytes)
        assert len(payload) > 0

    def test_deserialize_code__valid_bytes__reconstructs_code_type(self) -> None:
        """Verify deserialize_code unpacks marshaled bytes into an executable CodeType."""

        code = py_socket.compile_source("y = 50 * 2\n")
        payload = py_socket.serialize_code(code)

        reconstructed = py_socket.deserialize_code(payload)
        assert isinstance(reconstructed, types.CodeType)

        scope: dict[str, object] = {}
        exec(reconstructed, scope)
        assert scope["y"] == 100

    def test_deserialize_code__invalid_bytes__raises_value_error(self) -> None:
        """Verify deserialize_code raises ValueError when byte stream is corrupted."""

        with pytest.raises(ValueError, match="Failed to deserialize marshaled code"):
            py_socket.deserialize_code(b"\xff\x00\x12\x34not_marshal")

    def test_deserialize_code__non_code_marshal__raises_value_error(self) -> None:
        """Verify deserialize_code raises ValueError when payload marshals a non-code object."""

        payload = marshal.dumps(["not", "a", "code", "object"])

        with pytest.raises(ValueError, match="expected CodeType"):
            py_socket.deserialize_code(payload)

    def test_compile_and_serialize__round_trip__succeeds(self) -> None:
        """Verify compile_and_serialize completes the end-to-end compilation pipeline."""

        payload = py_socket.compile_and_serialize("msg = 'declusor_ok'\n", filename="<pipe>")
        code = py_socket.deserialize_code(payload)

        scope: dict[str, object] = {}
        exec(code, scope)
        assert scope["msg"] == "declusor_ok"

    def test_can_deserialize_code__valid_bytecode__returns_true(self) -> None:
        """Verify can_deserialize_code returns True for valid marshaled code objects."""

        payload = py_socket.compile_and_serialize("a = 1\n")

        assert py_socket.can_deserialize_code(payload) is True

    def test_can_deserialize_code__corrupted_bytes__returns_false(self) -> None:
        """Verify can_deserialize_code returns False for corrupted byte sequences."""

        assert py_socket.can_deserialize_code(b"corrupted") is False
        assert py_socket.can_deserialize_code(b"") is False

    def test_can_deserialize_code__marshaled_string__returns_false(self) -> None:
        """Verify can_deserialize_code returns False when payload is a marshaled string rather than a code object."""

        string_payload = marshal.dumps("just a string")

        assert py_socket.can_deserialize_code(string_payload) is False


class TestBytecodeCompatibility:
    """Tests for in_memory check_bytecode_compatibility function."""

    def test_check_bytecode_compatibility__matching_magic_and_version__returns_true(self) -> None:
        """Verify check_bytecode_compatibility returns True when magic and version match host."""

        magic = importlib.util.MAGIC_NUMBER
        version = list(sys.version_info[:3])

        compatible = py_socket.check_bytecode_compatibility(magic, version, platform.python_implementation())
        assert compatible is True

    def test_check_bytecode_compatibility__matching_hex_magic_and_version__returns_true(self) -> None:
        """Verify check_bytecode_compatibility accepts hex string magic numbers."""

        magic_hex = importlib.util.MAGIC_NUMBER.hex()
        version = tuple(sys.version_info[:2])

        compatible = py_socket.check_bytecode_compatibility(magic_hex, version)
        assert compatible is True

    def test_check_bytecode_compatibility__different_magic__returns_false(self) -> None:
        """Verify check_bytecode_compatibility returns False when magic number differs."""

        mismatched_magic = b"\x00\x00\x00\x00"

        compatible = py_socket.check_bytecode_compatibility(mismatched_magic, list(sys.version_info[:3]))
        assert compatible is False

    def test_check_bytecode_compatibility__different_version__returns_false(self) -> None:
        """Verify check_bytecode_compatibility returns False when minor version differs."""

        magic = importlib.util.MAGIC_NUMBER
        different_version = (sys.version_info.major, sys.version_info.minor + 1, 0)

        compatible = py_socket.check_bytecode_compatibility(magic, different_version)
        assert compatible is False

    def test_check_bytecode_compatibility__different_implementation__returns_false(self) -> None:
        """Verify check_bytecode_compatibility returns False for non-matching implementation."""

        magic = importlib.util.MAGIC_NUMBER
        version = list(sys.version_info[:3])

        compatible = py_socket.check_bytecode_compatibility(magic, version, client_implementation="PyPy")
        assert compatible is False

    def test_check_bytecode_compatibility__invalid_hex_string__returns_false(self) -> None:
        """Verify check_bytecode_compatibility returns False when hex string is invalid."""

        compatible = py_socket.check_bytecode_compatibility("invalid_hex!", list(sys.version_info[:3]))
        assert compatible is False

    def test_check_bytecode_compatibility__short_version_tuple__returns_false(self) -> None:
        """Verify check_bytecode_compatibility returns False when version tuple is too short."""

        magic = importlib.util.MAGIC_NUMBER
        compatible = py_socket.check_bytecode_compatibility(magic, [3])
        assert compatible is False
