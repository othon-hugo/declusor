"""Tests for the public exports of declusor.util."""

from declusor import util


class TestUtilExports:
    """Verify the canonical public utility API."""

    def test_util_exports__canonical_symbols__are_accessible(self) -> None:
        """Every declared public utility symbol is exported and accessible."""

        expected = [
            "ArgumentDefinitions",
            "await_connection",
            "build_command_parser",
            "convert_base64_to_bytes",
            "convert_bytes_to_hex",
            "convert_to_base64",
            "convert_to_bytes",
            "ensure_directory_exists",
            "ensure_file_exists",
            "find_plugin_entry",
            "format_template",
            "generate_nonce",
            "hash_md5",
            "hash_sha256",
            "hash_sha384",
            "hash_sha512",
            "import_plugin_from_file",
            "lang",
            "load_file",
            "parse_command_arguments",
            "ParsedArguments",
            "Parser",
            "quote",
            "Task",
            "TaskEvent",
            "TaskHandler",
            "TaskPool",
            "try_load_file",
            "validate_file_extension",
            "validate_file_relative",
            "xor_bytes",
        ]

        assert sorted(util.__all__) == sorted(expected)
        for symbol in expected:
            assert hasattr(util, symbol), f"declusor.util is missing export: {symbol}"
            assert not symbol.startswith("_")
