"""Tests for the public exports of declusor.command."""

from declusor import command


class TestCommandExports:
    """Verify the canonical public command API."""

    def test_command_exports__canonical_symbols__are_accessible(self) -> None:
        """Every declared public command symbol is exported and accessible."""

        expected = [
            "CommandError",
            "CommandValidationError",
            "EvaluateCode",
            "EvaluateCodeDTO",
            "ExecuteCommand",
            "ExecuteCommandDTO",
            "ExecuteFile",
            "ExecuteFileDTO",
            "InvalidOperation",
            "LaunchShell",
            "LaunchShellDTO",
            "LoadModule",
            "LoadModuleDTO",
            "UploadFile",
            "UploadFileDTO",
        ]

        assert sorted(command.__all__) == sorted(expected)
        for symbol in expected:
            assert hasattr(command, symbol), f"declusor.command is missing export: {symbol}"
            assert not symbol.startswith("_")
