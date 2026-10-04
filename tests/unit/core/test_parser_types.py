"""Unit tests for DeclusorParser argument types and validators in declusor.core.parser."""

from pathlib import Path

import pytest

from declusor import config, core


class TestDeclusorParserHost:
    """Tests verifying DeclusorParser.Host argument type validation."""

    def test_host__valid_ip_or_hostname__returns_host_instance(self) -> None:
        """Valid IP string or hostname produces a Host string subclass instance."""

        host = core.DeclusorParser.Host("127.0.0.1")

        assert host == "127.0.0.1"
        assert isinstance(host, core.DeclusorParser.Host)
        assert isinstance(host, str)

    def test_host__empty_string__raises_value_error(self) -> None:
        """Empty host string raises ValueError."""

        with pytest.raises(ValueError, match="host cannot be empty"):
            core.DeclusorParser.Host("")

    def test_host__metadata_constants__match_specifications(self) -> None:
        """Host defines expected arg_name and arg_help attributes."""

        assert core.DeclusorParser.Host.arg_name == "host"
        assert "IP address or hostname" in core.DeclusorParser.Host.arg_help


class TestDeclusorParserPort:
    """Tests verifying DeclusorParser.Port argument type validation."""

    def test_port__valid_integer_and_string__returns_port_instance(self) -> None:
        """Valid integer or numeric string produces a Port integer subclass instance."""

        port_int = core.DeclusorParser.Port(8080)
        port_str = core.DeclusorParser.Port("9000")

        assert port_int == 8080
        assert port_str == 9000
        assert isinstance(port_int, core.DeclusorParser.Port)
        assert isinstance(port_int, int)

    def test_port__boundary_zero_and_65535__are_valid(self) -> None:
        """Ports 0 and 65535 are accepted boundaries."""

        assert core.DeclusorParser.Port(0) == 0
        assert core.DeclusorParser.Port(65535) == 65535

    def test_port__negative_port__raises_value_error(self) -> None:
        """Negative port numbers raise ValueError."""

        with pytest.raises(ValueError, match="port must be between 0 and 65535"):
            core.DeclusorParser.Port(-1)

    def test_port__port_exceeding_65535__raises_value_error(self) -> None:
        """Port numbers exceeding 65535 raise ValueError."""

        with pytest.raises(ValueError, match="port must be between 0 and 65535"):
            core.DeclusorParser.Port(65536)

    def test_port__non_numeric_string__raises_value_error(self) -> None:
        """Non-numeric string values raise ValueError during conversion."""

        with pytest.raises(ValueError):
            core.DeclusorParser.Port("invalid_port")

    def test_port__metadata_constants__match_specifications(self) -> None:
        """Port defines expected arg_name and arg_help attributes."""

        assert core.DeclusorParser.Port.arg_name == "port"
        assert "port number to listen on" in core.DeclusorParser.Port.arg_help


class TestDeclusorParserPlugin:
    """Tests verifying DeclusorParser.Plugin argument type validation."""

    def test_plugin__valid_string__returns_plugin_instance(self) -> None:
        """Valid plugin identifier produces a Plugin string subclass instance."""

        plugin = core.DeclusorParser.Plugin("shell_socket")

        assert plugin == "shell_socket"
        assert isinstance(plugin, core.DeclusorParser.Plugin)

    def test_plugin__empty_string__raises_value_error(self) -> None:
        """Empty plugin name raises ValueError."""

        with pytest.raises(ValueError, match="plugin cannot be empty"):
            core.DeclusorParser.Plugin("")

    def test_plugin__metadata_constants__match_specifications(self) -> None:
        """Plugin defines expected flags and help attributes."""

        assert core.DeclusorParser.Plugin.arg_name == "plugin"
        assert core.DeclusorParser.Plugin.arg_flags == ("-p", "--plugin")
        assert "agent responsible for handling requests" in core.DeclusorParser.Plugin.arg_help


class TestDeclusorParserAssetsAndPluginDir:
    """Tests verifying DeclusorParser.AssetsDir and PluginDir argument definitions."""

    def test_assets_dir__path_subclass_and_metadata(self) -> None:
        """AssetsDir is a Path subclass with correct argument attributes."""

        path = core.DeclusorParser.AssetsDir("/path/to/assets")

        assert isinstance(path, Path)
        assert core.DeclusorParser.AssetsDir.arg_name == "assets_dir"
        assert core.DeclusorParser.AssetsDir.arg_flags == ("--assets-dir",)

    def test_plugin_dir__path_subclass_and_metadata(self) -> None:
        """PluginDir is a Path subclass with correct argument attributes."""

        path = core.DeclusorParser.PluginDir("/path/to/plugins")

        assert isinstance(path, Path)
        assert core.DeclusorParser.PluginDir.arg_name == "plugin_dir"
        assert core.DeclusorParser.PluginDir.arg_flags == ("--plugin-dir",)


class TestDeclusorParserExecutionMode:
    """Tests verifying DeclusorParser.ExecutionMode argument type validation."""

    @pytest.mark.parametrize("mode_name", ["cli", "api", "mcp", "http"])
    def test_execution_mode__valid_choices__returns_execution_mode_instance(self, mode_name: str) -> None:
        """Valid execution modes return string subclass instances matching their enum values."""

        mode = core.DeclusorParser.ExecutionMode(mode_name)

        assert mode == mode_name
        assert isinstance(mode, core.DeclusorParser.ExecutionMode)

    def test_execution_mode__empty_string__raises_value_error(self) -> None:
        """Empty execution mode string raises ValueError."""

        with pytest.raises(ValueError, match="execution mode cannot be empty"):
            core.DeclusorParser.ExecutionMode("")

    def test_execution_mode__invalid_choice__raises_value_error_with_choices(self) -> None:
        """Unrecognized execution mode raises ValueError indicating valid choices."""

        with pytest.raises(ValueError, match="invalid choice: 'grpc'"):
            core.DeclusorParser.ExecutionMode("grpc")

    def test_execution_mode__metadata_constants__match_specifications(self) -> None:
        """ExecutionMode defines expected flags, choices, and default."""

        assert core.DeclusorParser.ExecutionMode.arg_name == "mode"
        assert core.DeclusorParser.ExecutionMode.arg_flags == ("-m", "--mode")
        assert core.DeclusorParser.ExecutionMode.arg_default == config.DEFAULT_EXECUTION_MODE


class TestDeclusorParserLauncherOutput:
    """Tests verifying DeclusorParser.LauncherOutput argument type validation."""

    def test_launcher_output__terminal_string__returns_terminal_mode(self) -> None:
        """'terminal' in any case returns normalized 'terminal' mode string."""

        assert core.DeclusorParser.LauncherOutput("terminal") == "terminal"
        assert core.DeclusorParser.LauncherOutput("TERMINAL") == "terminal"

    def test_launcher_output__silent_string__returns_silent_mode(self) -> None:
        """'silent' in any case returns normalized 'silent' mode string."""

        assert core.DeclusorParser.LauncherOutput("silent") == "silent"
        assert core.DeclusorParser.LauncherOutput("Silent") == "silent"

    def test_launcher_output__file_with_valid_path__returns_normalized_file_string(self) -> None:
        """'file:<path>' returns the normalized file path specification string."""

        output = core.DeclusorParser.LauncherOutput("file:/tmp/out.sh")

        assert output == "file:/tmp/out.sh"

    def test_launcher_output__file_with_empty_path__raises_value_error(self) -> None:
        """'file:' without a destination path raises ValueError."""

        with pytest.raises(ValueError, match="output path cannot be empty"):
            core.DeclusorParser.LauncherOutput("file:")

        with pytest.raises(ValueError, match="output path cannot be empty"):
            core.DeclusorParser.LauncherOutput("file:   ")

    def test_launcher_output__empty_string__raises_value_error(self) -> None:
        """Empty launcher output string raises ValueError."""

        with pytest.raises(ValueError, match="launcher output cannot be empty"):
            core.DeclusorParser.LauncherOutput("")

    def test_launcher_output__invalid_output_mode__raises_value_error(self) -> None:
        """Unrecognized launcher output mode string raises ValueError."""

        with pytest.raises(ValueError, match="invalid launcher output mode: 'network'"):
            core.DeclusorParser.LauncherOutput("network")

    def test_launcher_output__metadata_constants__match_specifications(self) -> None:
        """LauncherOutput defines expected flags and default."""

        assert core.DeclusorParser.LauncherOutput.arg_name == "launcher_output"
        assert core.DeclusorParser.LauncherOutput.arg_flags == ("-o", "--launcher-output")
        assert core.DeclusorParser.LauncherOutput.arg_default == config.DEFAULT_LAUNCHER_OUTPUT_MODE.value


class TestDeclusorParserLauncherWrapper:
    """Tests verifying DeclusorParser.LauncherWrapper argument type validation."""

    def test_launcher_wrapper__valid_template__returns_wrapper_instance(self) -> None:
        """Valid shell wrapper template returns a LauncherWrapper instance."""

        wrapper = core.DeclusorParser.LauncherWrapper("python3 -c '$DECLUSOR_SCRIPT'")

        assert wrapper == "python3 -c '$DECLUSOR_SCRIPT'"
        assert isinstance(wrapper, core.DeclusorParser.LauncherWrapper)

    def test_launcher_wrapper__empty_string__raises_value_error(self) -> None:
        """Empty launcher wrapper string raises ValueError."""

        with pytest.raises(ValueError, match="launcher wrapper cannot be empty"):
            core.DeclusorParser.LauncherWrapper("")

    def test_launcher_wrapper__metadata_constants__match_specifications(self) -> None:
        """LauncherWrapper defines expected flags and help attributes."""

        assert core.DeclusorParser.LauncherWrapper.arg_name == "launcher_wrapper"
        assert core.DeclusorParser.LauncherWrapper.arg_flags == ("-w", "--launcher-wrapper")


class TestDeclusorParserTimeout:
    """Tests verifying DeclusorParser.Timeout argument type validation."""

    def test_timeout__positive_float_and_int__returns_timeout_instance(self) -> None:
        """Positive float and int values produce a Timeout float subclass instance."""

        t1 = core.DeclusorParser.Timeout(5.5)
        t2 = core.DeclusorParser.Timeout("10.0")

        assert t1 == 5.5
        assert t2 == 10.0
        assert isinstance(t1, core.DeclusorParser.Timeout)
        assert isinstance(t1, float)

    def test_timeout__zero__raises_value_error(self) -> None:
        """A timeout of zero raises ValueError."""

        with pytest.raises(ValueError, match="timeout must be greater than 0"):
            core.DeclusorParser.Timeout(0)

    def test_timeout__negative_float__raises_value_error(self) -> None:
        """Negative timeout values raise ValueError."""

        with pytest.raises(ValueError, match="timeout must be greater than 0"):
            core.DeclusorParser.Timeout(-2.5)

    def test_timeout__non_numeric_string__raises_value_error(self) -> None:
        """Non-numeric string values raise ValueError."""

        with pytest.raises(ValueError, match="invalid timeout value: 'abc'"):
            core.DeclusorParser.Timeout("abc")

    def test_timeout__metadata_constants__match_specifications(self) -> None:
        """Timeout defines expected flags and help attributes."""

        assert core.DeclusorParser.Timeout.arg_name == "timeout"
        assert core.DeclusorParser.Timeout.arg_flags == ("-t", "--timeout")


class TestDeclusorParserTransportLayer:
    """Tests verifying DeclusorParser.TransportLayer argument type validation."""

    def test_transport_layer__valid_identifier__normalizes_and_lowercases(self) -> None:
        """Valid transport layer names are stripped and converted to lowercase."""

        layer = core.DeclusorParser.TransportLayer("  XOR  ")

        assert layer == "xor"
        assert isinstance(layer, core.DeclusorParser.TransportLayer)

    def test_transport_layer__empty_or_whitespace_only__raises_value_error(self) -> None:
        """Empty or whitespace-only transport layer names raise ValueError."""

        with pytest.raises(ValueError, match="transport layer name cannot be empty"):
            core.DeclusorParser.TransportLayer("")

        with pytest.raises(ValueError, match="transport layer name cannot be empty"):
            core.DeclusorParser.TransportLayer("   ")

    def test_transport_layer__metadata_constants__match_specifications(self) -> None:
        """TransportLayer defines expected flags, action, and name attributes."""

        assert core.DeclusorParser.TransportLayer.arg_name == "transport_layers"
        assert core.DeclusorParser.TransportLayer.arg_flags == ("-l", "--transport-layer")
        assert core.DeclusorParser.TransportLayer.arg_action == "append"


class TestDeclusorParserParseLauncherOutputStaticMethod:
    """Tests verifying DeclusorParser.parse_launcher_output static conversion method."""

    def test_parse_launcher_output__terminal__returns_terminal_mode_and_none_path(self) -> None:
        """'terminal' returns LauncherOutputMode.TERMINAL and None destination path."""

        mode, path = core.DeclusorParser.parse_launcher_output("terminal")

        assert mode == config.LauncherOutputMode.TERMINAL
        assert path is None

    def test_parse_launcher_output__silent__returns_silent_mode_and_none_path(self) -> None:
        """'silent' returns LauncherOutputMode.SILENT and None destination path."""

        mode, path = core.DeclusorParser.parse_launcher_output("silent")

        assert mode == config.LauncherOutputMode.SILENT
        assert path is None

    def test_parse_launcher_output__file_path__returns_file_mode_and_path(self) -> None:
        """'file:<path>' returns LauncherOutputMode.FILE and resolved Path object."""

        mode, path = core.DeclusorParser.parse_launcher_output("file:/tmp/out/launcher.sh")

        assert mode == config.LauncherOutputMode.FILE
        assert path == Path("/tmp/out/launcher.sh")

    def test_parse_launcher_output__invalid_value__raises_value_error(self) -> None:
        """Any invalid mode string raises ValueError."""

        with pytest.raises(ValueError, match="invalid launcher output mode: 'unsupported'"):
            core.DeclusorParser.parse_launcher_output("unsupported")
