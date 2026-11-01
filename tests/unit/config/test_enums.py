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
        assert config.LauncherOutputMode.CLIPBOARD.value == "clipboard"
        assert len(config.LauncherOutputMode) == 4

    def test_launcher_output_mode__subclass__is_str_enum(self) -> None:
        """Verify LauncherOutputMode is a StrEnum that behaves as a string."""

        assert issubclass(config.LauncherOutputMode, StrEnum)
        assert isinstance(config.LauncherOutputMode.TERMINAL, str)
        assert config.LauncherOutputMode.TERMINAL.value == "terminal"
        assert isinstance(config.LauncherOutputMode.CLIPBOARD, str)
        assert config.LauncherOutputMode.CLIPBOARD.value == "clipboard"


class TestLauncherKindEnum:
    """Tests for LauncherKind enumeration and string parsing."""

    def test_launcher_kind__members__match_expected_string_values(self) -> None:
        """Verify LauncherKind members map to expected string identifiers."""

        assert config.LauncherKind.STAGED.value == "staged"
        assert config.LauncherKind.STAGELESS.value == "stageless"
        assert len(config.LauncherKind) == 2

    def test_launcher_kind__subclass__is_str_enum(self) -> None:
        """Verify LauncherKind is a StrEnum that behaves as a string."""

        assert issubclass(config.LauncherKind, StrEnum)
        assert isinstance(config.LauncherKind.STAGED, str)
        assert config.LauncherKind.STAGED.value == "staged"

    @pytest.mark.parametrize(
        ("input_str", "expected_kind"),
        [
            ("staged", config.LauncherKind.STAGED),
            ("stageless", config.LauncherKind.STAGELESS),
        ],
    )
    def test_launcher_kind_from_string__exact_case__returns_matching_member(
        self,
        input_str: str,
        expected_kind: config.LauncherKind,
    ) -> None:
        """Verify from_string parses exact lowercase strings."""

        assert config.LauncherKind.from_string(input_str) == expected_kind

    @pytest.mark.parametrize(
        ("input_str", "expected_kind"),
        [
            ("STAGED", config.LauncherKind.STAGED),
            ("  Staged  ", config.LauncherKind.STAGED),
            ("STAGELESS", config.LauncherKind.STAGELESS),
            (" \n stageless \t", config.LauncherKind.STAGELESS),
        ],
    )
    def test_launcher_kind_from_string__case_insensitive_and_whitespace__normalizes_and_returns_member(
        self,
        input_str: str,
        expected_kind: config.LauncherKind,
    ) -> None:
        """Verify from_string normalizes whitespace and uppercase input."""

        assert config.LauncherKind.from_string(input_str) == expected_kind

    def test_launcher_kind_from_string__unrecognized_string__raises_value_error_with_choices(self) -> None:
        """Verify from_string raises ValueError listing valid launcher kinds."""

        with pytest.raises(
            ValueError,
            match=r"Invalid launcher kind: 'unsupported'\. Valid choices: 'staged', 'stageless'",
        ):
            config.LauncherKind.from_string("unsupported")

    def test_launcher_kind_from_string__empty_string__raises_value_error(self) -> None:
        """Verify from_string raises ValueError on empty string input."""

        with pytest.raises(ValueError, match="Invalid launcher kind: ''"):
            config.LauncherKind.from_string("")


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
        assert config.ChannelType.STDIN.value == 3
        assert config.ChannelType.SIGNAL.value == 4
        assert config.ChannelType.HEARTBEAT.value == 5
        assert len(config.ChannelType) == 6

    def test_channel_type__subclass__is_int_enum(self) -> None:
        """Verify ChannelType is an IntEnum that behaves as an integer."""

        assert issubclass(config.ChannelType, IntEnum)
        assert isinstance(config.ChannelType.STDOUT, int)
        assert config.ChannelType.STDOUT.value == 1


class TestExitCodeEnum:
    """Tests for ExitCode enumeration."""

    def test_exit_code__members__match_expected_int_values(self) -> None:
        """Verify ExitCode members map to standard UNIX/POSIX process exit codes."""

        assert config.ExitCode.SUCCESS.value == 0
        assert config.ExitCode.FAILURE.value == 1
        assert config.ExitCode.USAGE_ERROR.value == 2
        assert len(config.ExitCode) == 3

    def test_exit_code__subclass__is_int_enum(self) -> None:
        """Verify ExitCode is an IntEnum."""

        assert issubclass(config.ExitCode, IntEnum)


class TestCoreRouteEnum:
    """Tests for CoreRoute enumeration."""

    def test_core_route__members__match_expected_string_values(self) -> None:
        """Verify CoreRoute members map to reserved route names."""

        assert config.CoreRoute.HELP.value == "help"
        assert config.CoreRoute.EXIT.value == "exit"
        assert len(config.CoreRoute) == 2

    def test_core_route__subclass__is_str_enum(self) -> None:
        """Verify CoreRoute is a StrEnum."""

        assert issubclass(config.CoreRoute, StrEnum)


class TestOfficialRouteEnum:
    """Tests for OfficialRoute enumeration."""

    def test_official_route__members__match_expected_string_values(self) -> None:
        """Verify OfficialRoute members map to standard plugin routes."""

        assert config.OfficialRoute.LOAD.value == "load"
        assert config.OfficialRoute.COMMAND.value == "command"
        assert config.OfficialRoute.EVAL.value == "eval"
        assert config.OfficialRoute.SHELL.value == "shell"
        assert config.OfficialRoute.UPLOAD.value == "upload"
        assert config.OfficialRoute.EXECUTE.value == "execute"
        assert len(config.OfficialRoute) == 6

    def test_official_route__subclass__is_str_enum(self) -> None:
        """Verify OfficialRoute is a StrEnum."""

        assert issubclass(config.OfficialRoute, StrEnum)


class TestRouteCompletionModeEnum:
    """Tests for RouteCompletionMode enumeration."""

    def test_route_completion_mode__members__match_expected_string_values(self) -> None:
        """Verify RouteCompletionMode members map to expected string identifiers."""

        assert config.RouteCompletionMode.NONE.value == "none"
        assert config.RouteCompletionMode.HOST_PATH.value == "host_path"
        assert config.RouteCompletionMode.MODULE_PATH.value == "module_path"
        assert config.RouteCompletionMode.ASSET_PATH.value == "asset_path"
        assert len(config.RouteCompletionMode) == 4

    def test_route_completion_mode__subclass__is_str_enum(self) -> None:
        """Verify RouteCompletionMode is a StrEnum."""

        assert issubclass(config.RouteCompletionMode, StrEnum)


class TestTransportLayerEnum:
    """Tests for TransportLayer enumeration."""

    def test_transport_layer__members__match_expected_string_values(self) -> None:
        """Verify TransportLayer members map to recognized transport layer names."""

        assert config.TransportLayer.XOR.value == "xor"
        assert len(config.TransportLayer) == 1

    def test_transport_layer__subclass__is_str_enum(self) -> None:
        """Verify TransportLayer is a StrEnum."""

        assert issubclass(config.TransportLayer, StrEnum)
