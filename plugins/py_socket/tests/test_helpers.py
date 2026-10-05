import base64
import importlib.util
import marshal
from pathlib import Path
from types import ModuleType

import pytest


def _load_std_helper_module() -> ModuleType:
    helper_path = Path(__file__).parent.parent / "assets" / "helpers" / "std.py"
    spec = importlib.util.spec_from_file_location("py_socket_helper_std", helper_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


std_helpers = _load_std_helper_module()


class TestPySocketStdHelpersEncoding:
    """Unit tests for encoding and decoding primitives."""

    def test_decode_base64__empty_input__returns_empty_bytes(self) -> None:
        """Verify empty input to decode_base64 returns empty bytes."""

        assert std_helpers.decode_base64("") == b""
        assert std_helpers.decode_base64(b"") == b""

    def test_decode_base64__valid_input__decodes_to_bytes(self) -> None:
        """Verify valid Base64 string or bytes decodes to raw bytes."""

        raw = b"hello declusor"
        b64_str = base64.b64encode(raw).decode("ascii")

        assert std_helpers.decode_base64(b64_str) == raw
        assert std_helpers.decode_base64(b64_str.encode("ascii")) == raw

    def test_encode_base64__valid_input__encodes_to_ascii_string(self) -> None:
        """Verify encode_base64 converts bytes to an ASCII string."""

        raw = b"test payload 123"
        expected = base64.b64encode(raw).decode("ascii")

        assert std_helpers.encode_base64(raw) == expected

    def test_hash_value__string_and_bytes__produces_matching_sha256(self) -> None:
        """Verify hash_value calculates deterministic SHA-256 for strings and bytes."""

        h1 = std_helpers.hash_value("sample text")
        h2 = std_helpers.hash_value(b"sample text")

        assert h1 == h2
        assert len(h1) == 64


class TestPySocketStdHelpersStorage:
    """Unit tests for storage and removal primitives."""

    def test_store_file__with_target_path__writes_bytes_and_returns_path(self, tmp_path: Path) -> None:
        """Verify store_file writes raw bytes to the specified target path."""

        target = tmp_path / "out.bin"
        content = b"stored binary content"

        result_path = std_helpers.store_file(content, str(target))

        assert result_path == str(target)
        assert target.read_bytes() == content

    def test_store_file__without_target_path__generates_temp_file(self) -> None:
        """Verify store_file generates an ephemeral path when target_path is omitted."""

        content = b"ephemeral content 456"
        result_path = std_helpers.store_file(content)

        try:
            assert Path(result_path).exists()
            assert Path(result_path).read_bytes() == content
        finally:
            std_helpers.remove_file(result_path)

    def test_remove_file__existing_and_nonexistent__handles_safely(self, tmp_path: Path) -> None:
        """Verify remove_file unlinks existing file and suppresses errors on nonexistent paths."""

        test_file = tmp_path / "to_delete.txt"
        test_file.write_text("temporary")
        assert test_file.exists()

        std_helpers.remove_file(str(test_file))
        assert not test_file.exists()

        # Should not raise for non-existent file
        std_helpers.remove_file(str(tmp_path / "nonexistent.bin"))


class TestPySocketStdHelpersExecution:
    """Unit tests for execution primitives."""

    def test_execute_source__valid_code__executes_in_scope(self) -> None:
        """Verify execute_source compiles and executes Python code in globals."""

        std_helpers.execute_source("foo_var = 12345")
        assert getattr(std_helpers, "foo_var", None) == 12345

    def test_execute_source__syntax_error__handles_cleanly(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Verify execute_source catches and prints syntax errors without terminating."""

        std_helpers.execute_source("def invalid syntax:")
        captured = capsys.readouterr()
        assert "[py_socket error] SyntaxError:" in captured.err

    def test_execute_bytecode__valid_code_object__executes_in_scope(self) -> None:
        """Verify execute_bytecode unmarshals and executes serialized bytecode."""

        code = compile("marshaled_var = 9999", "<test>", "exec")
        code_bytes = marshal.dumps(code)

        std_helpers.execute_bytecode(code_bytes)
        assert getattr(std_helpers, "marshaled_var", None) == 9999

    def test_execute_binary__executable_script__runs_and_cleans_up(self, tmp_path: Path) -> None:
        """Verify execute_binary executes binary payload and cleans up when cleanup=True."""

        script_path = tmp_path / "test_exec.sh"
        script_path.write_text("#!/bin/sh\necho 'binary execution ok'\n")

        std_helpers.execute_binary(str(script_path), cleanup=True)
        assert not script_path.exists()

    def test_execute_system_command__runs_shell_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Verify execute_system_command runs shell commands and flushes stdout."""

        std_helpers.execute_system_command("echo 'test system command'")
        captured = capsys.readouterr()
        assert "test system command" in captured.out


class TestPySocketStdHelpersUtilities:
    """Unit tests for presentation and diagnostic utility helpers."""

    def test_label__prints_header_and_content(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Verify label outputs uppercase title with underline and content."""

        std_helpers.label("Status", "All systems operational")
        captured = capsys.readouterr()
        assert "STATUS" in captured.out
        assert "------" in captured.out
        assert "All systems operational" in captured.out

    def test_format_table__formats_aligned_columns(self) -> None:
        """Verify format_table formats headers and rows with aligned column padding."""

        headers = ["ID", "Name", "Status"]
        rows = [["1", "Alice", "Active"], ["2", "Bob", "Pending"]]
        table = std_helpers.format_table(headers, rows)

        assert "ID  Name   Status" in table
        assert "1   Alice  Active" in table
        assert "2   Bob    Pending" in table

    def test_get_system_summary__returns_required_keys(self) -> None:
        """Verify get_system_summary returns system diagnostic dictionary with expected keys."""

        summary = std_helpers.get_system_summary()
        assert isinstance(summary, dict)
        assert "platform" in summary
        assert "architecture" in summary
        assert "release" in summary
        assert "python_version" in summary
        assert "username" in summary
        assert "pid" in summary
