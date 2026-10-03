"""Unit tests for framework configuration and domain enums."""

from enum import IntEnum, StrEnum

import pytest

from declusor import config


class TestDeclusorPluginsEnum:
    """Tests for DeclusorPlugins enumeration."""

    def test_declusor_plugins__members__match_expected_string_values(self) -> None:
        """Verify DeclusorPlugins members map to their registered string identifiers."""

        assert config.DeclusorPlugins.SHELL_SOCKET.value == "shell_socket"
        assert config.DeclusorPlugins.PY_SOCKET.value == "py_socket"
        assert len(config.DeclusorPlugins) == 2

    def test_declusor_plugins__subclass__is_str_enum(self) -> None:
        """Verify DeclusorPlugins is a StrEnum that behaves as a string."""

        assert issubclass(config.DeclusorPlugins, StrEnum)
        assert isinstance(config.DeclusorPlugins.SHELL_SOCKET, str)
        assert config.DeclusorPlugins.SHELL_SOCKET.value == "shell_socket"


class TestLauncherOutputModeEnum:
    """Tests for LauncherOutputMode enumeration."""

    def test_launcher_output_mode__members__match_expected_string_values(self) -> None:
        """Verify LauncherOutputMode members map to expected string identifiers."""

        assert config.LauncherOutputMode.TERMINAL.value == "terminal"
        assert config.LauncherOutputMode.SILENT.value == "silent"
        assert config.LauncherOutputMode.FILE.value == "file"
        assert len(config.LauncherOutputMode) == 3

    def test_launcher_output_mode__subclass__is_str_enum(self) -> None:
        """Verify LauncherOutputMode is a StrEnum that behaves as a string."""

        assert issubclass(config.LauncherOutputMode, StrEnum)
        assert isinstance(config.LauncherOutputMode.TERMINAL, str)
        assert config.LauncherOutputMode.TERMINAL.value == "terminal"


class TestExecutionModeEnum:
    """Tests for ExecutionMode enumeration and string parsing."""

    def test_execution_mode__members__match_expected_string_values(self) -> None:
        """Verify ExecutionMode members map to expected string modes."""

        assert config.ExecutionMode.CLI.value == "cli"
        assert config.ExecutionMode.API.value == "api"
        assert config.ExecutionMode.MCP.value == "mcp"
        assert config.ExecutionMode.HTTP.value == "http"
        assert len(config.ExecutionMode) == 4

    @pytest.mark.parametrize(
        ("input_str", "expected_mode"),
        [
            ("cli", config.ExecutionMode.CLI),
            ("api", config.ExecutionMode.API),
            ("mcp", config.ExecutionMode.MCP),
            ("http", config.ExecutionMode.HTTP),
        ],
    )
    def test_execution_mode_from_string__exact_case__returns_matching_member(self, input_str: str, expected_mode: config.ExecutionMode) -> None:
        """Verify from_string parses exact lowercase strings."""

        assert config.ExecutionMode.from_string(input_str) == expected_mode

    @pytest.mark.parametrize(
        ("input_str", "expected_mode"),
        [
            ("CLI", config.ExecutionMode.CLI),
            ("  Cli  ", config.ExecutionMode.CLI),
            ("API", config.ExecutionMode.API),
            ("  api \t", config.ExecutionMode.API),
            ("Mcp", config.ExecutionMode.MCP),
            ("  MCP  ", config.ExecutionMode.MCP),
            ("HTTP", config.ExecutionMode.HTTP),
            (" \n http \t", config.ExecutionMode.HTTP),
        ],
    )
    def test_execution_mode_from_string__case_insensitive_and_whitespace__normalizes_and_returns_member(
        self, input_str: str, expected_mode: config.ExecutionMode
    ) -> None:
        """Verify from_string normalizes whitespace and uppercase input."""

        assert config.ExecutionMode.from_string(input_str) == expected_mode

    def test_execution_mode_from_string__unrecognized_string__raises_value_error_with_choices(self) -> None:
        """Verify from_string raises ValueError listing valid execution modes."""

        with pytest.raises(
            ValueError,
            match=r"Invalid execution mode: 'unsupported'\. Choose from: 'cli', 'api', 'mcp', 'http'",
        ):
            config.ExecutionMode.from_string("unsupported")

    def test_execution_mode_from_string__empty_string__raises_value_error(self) -> None:
        """Verify from_string raises ValueError on empty string input."""

        with pytest.raises(ValueError, match="Invalid execution mode: ''"):
            config.ExecutionMode.from_string("")

    def test_execution_mode_from_string__whitespace_only__raises_value_error(self) -> None:
        """Verify from_string raises ValueError on whitespace-only input."""

        with pytest.raises(ValueError, match=r"Invalid execution mode: '   '"):
            config.ExecutionMode.from_string("   ")


class TestOperationCodeEnum:
    """Tests for OperationCode enumeration."""

    def test_operation_code__members__match_expected_string_values(self) -> None:
        """Verify OperationCode members match exact protocol command strings."""

        assert config.OperationCode.EXEC_COMMAND.value == "EXECUTE_COMMAND"
        assert config.OperationCode.EXEC_CODE.value == "EXECUTE_CODE"
        assert config.OperationCode.EXEC_FILE.value == "EXECUTE_FILE"
        assert config.OperationCode.STORE_FILE.value == "STORE_FILE"
        assert config.OperationCode.LOAD_MODULE.value == "LOAD_MODULE"
        assert len(config.OperationCode) == 5

    def test_operation_code__subclass__is_str_enum(self) -> None:
        """Verify OperationCode is a StrEnum that behaves as a string."""

        assert issubclass(config.OperationCode, StrEnum)
        assert isinstance(config.OperationCode.EXEC_COMMAND, str)
        assert config.OperationCode.EXEC_COMMAND.value == "EXECUTE_COMMAND"


class TestFramingModeEnum:
    """Tests for FramingMode enumeration."""

    def test_framing_mode__members__match_expected_string_values(self) -> None:
        """Verify FramingMode members match expected stream framing names."""

        assert config.FramingMode.SENTINEL.value == "sentinel"
        assert config.FramingMode.CHUNKED_TLV.value == "chunked_tlv"
        assert config.FramingMode.EPHEMERAL_ENVELOPE.value == "ephemeral_envelope"
        assert len(config.FramingMode) == 3

    def test_framing_mode__subclass__is_str_enum(self) -> None:
        """Verify FramingMode is a StrEnum that behaves as a string."""

        assert issubclass(config.FramingMode, StrEnum)
        assert isinstance(config.FramingMode.CHUNKED_TLV, str)
        assert config.FramingMode.CHUNKED_TLV.value == "chunked_tlv"


class TestChannelTypeEnum:
    """Tests for ChannelType multiplexing enumeration."""

    def test_channel_type__members__match_expected_int_values(self) -> None:
        """Verify ChannelType members match integer channel identifiers."""

        assert config.ChannelType.PROCESS_EXIT.value == 0
        assert config.ChannelType.STDOUT.value == 1
        assert config.ChannelType.STDERR.value == 2
        assert config.ChannelType.SIGNAL.value == 3
        assert config.ChannelType.HEARTBEAT.value == 4
        assert len(config.ChannelType) == 5

    def test_channel_type__subclass__is_int_enum(self) -> None:
        """Verify ChannelType is an IntEnum that behaves as an integer."""

        assert issubclass(config.ChannelType, IntEnum)
        assert isinstance(config.ChannelType.STDOUT, int)
        assert config.ChannelType.STDOUT.value == 1
