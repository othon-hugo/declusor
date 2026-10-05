"""Unit tests for DeclusorParser argument parsing and configuration assembly in declusor.core.parser."""

from collections.abc import Mapping
from pathlib import Path

import pytest

from declusor import config, contract, core, testing, transport


class DummyPathConfig(contract.ParsedArguments, total=False):
    """Configuration options for DummyPathClientPlugin."""

    launcher_path: Path


class DummyPathClientPlugin(contract.IPluginExtension[DummyPathConfig]):
    """Dummy client plugin for testing data path derivation."""

    name = "dummy_path_plugin"
    description = "Dummy path client"
    version = "1.0.0"
    options_type = DummyPathConfig
    supported_controllers = frozenset()

    @classmethod
    def configure_parser(cls, parser: contract.IArgumentParser, /) -> None:
        pass

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> DummyPathConfig:
        return DummyPathConfig()

    @classmethod
    def build_config(
        cls,
        host: str,
        port: int,
        options: DummyPathConfig,
        /,
        filesystem: contract.PluginFilesystem | None = None,
        mode: config.ExecutionMode = config.DEFAULT_EXECUTION_MODE,
    ) -> contract.PluginConfig[DummyPathConfig]:
        assert filesystem is not None

        launcher = filesystem.launchers / "client.sh"
        options["launcher_path"] = launcher

        return contract.PluginConfig(
            kind=cls.name,
            host=host,
            port=port,
            filesystem=filesystem,
            options=options,
            options_type=cls.options_type,
            mode=mode,
        )

    @classmethod
    def validate(cls, plugin_config: contract.PluginConfig[DummyPathConfig], /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config: contract.PluginConfig[DummyPathConfig], /) -> contract.IPluginRuntime:
        return testing.DummyPluginRuntime()


class TestDeclusorParserInitialization:
    """Tests verifying DeclusorParser initialization and base configuration."""

    def test_parser__init__sets_prog_and_description(self) -> None:
        """DeclusorParser initializes with prog and description attributes."""

        parser = core.DeclusorParser(name="test_app", description="test description")

        assert parser.prog == "test_app"
        assert parser.description == "test description"

    def test_parser__init_empty_description__normalizes_description_to_none(self) -> None:
        """DeclusorParser sets description to None when given an empty string."""

        parser = core.DeclusorParser(name="test_app", description="")

        assert parser.description is None

    def test_parser__configure_common_arguments__is_idempotent(self) -> None:
        """Calling _configure_common_arguments multiple times does not duplicate arguments."""

        parser = core.DeclusorParser(name="test_app")

        # Second call should return early
        parser._configure_common_arguments()

        assert parser._is_configured is True


class TestDeclusorParserLifecycle:
    """Tests verifying parse execution and configuration building lifecycle."""

    def test_parse__valid_minimal_cli_arguments__builds_plugin_config(self, tmp_path: Path) -> None:
        """Parsing minimal valid arguments builds a populated PluginConfig."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(
            manager,
            ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "--assets-dir", str(tmp_path)],
        )

        assert plugin_config.host == "127.0.0.1"
        assert plugin_config.port == 9000
        assert plugin_config.kind == testing.DummyPlugin.name
        assert plugin_config.filesystem is not None
        assert plugin_config.filesystem.root == tmp_path.resolve()
        assert parser in testing.DummyPlugin.configured_parsers

    def test_parse__missing_host_or_port__raises_parser_error(self) -> None:
        """Omitting required positional host or port arguments raises ParserError."""

        manager = core.PluginManager()
        parser = core.DeclusorParser(name="test_app")

        with pytest.raises(config.ParserError):
            parser.parse(manager, ["127.0.0.1"])  # missing port

    def test_parse__repeated_parse_calls_on_same_instance__is_idempotent(self, tmp_path: Path) -> None:
        """Calling parse() repeatedly on the same parser instance operates idempotently."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        argv = ["127.0.0.1", "8080", "--plugin", testing.DummyPlugin.name, "--assets-dir", str(tmp_path)]
        parser = core.DeclusorParser(name="test_app")

        config1 = parser.parse(manager, argv)
        config2 = parser.parse(manager, argv)

        assert config1.host == config2.host == "127.0.0.1"
        assert config1.port == config2.port == 8080

    def test_parse__custom_assets_dir__builds_plugin_filesystem_from_root(self, tmp_path: Path) -> None:
        """When --assets-dir is specified, plugin configuration derives paths from that root."""

        assets_dir = tmp_path / "assets"
        launcher_dir = assets_dir / "launchers"
        launcher_dir.mkdir(parents=True)
        launcher_file = launcher_dir / "client.sh"
        launcher_file.write_text("", encoding="utf-8")

        manager = core.PluginManager()
        manager.register(DummyPathClientPlugin)

        parser = core.DeclusorParser(name="declusor")
        plugin_config = parser.parse(
            manager,
            ["127.0.0.1", "9000", "--plugin", "dummy_path_plugin", "--assets-dir", str(tmp_path)],
        )

        assert plugin_config.filesystem == contract.PluginFilesystem.from_root(tmp_path)
        assert plugin_config.options.get("launcher_path") == launcher_file

    def test_parse__omitted_assets_dir__preserves_plugin_default_filesystem(self) -> None:
        """When --assets-dir is omitted, the plugin falls back to its default filesystem."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name])

        assert plugin_config.filesystem is not None

    def test_parse__cli_plugin_dir__dynamically_loads_and_registers_plugins(self, tmp_path: Path) -> None:
        """Specifying --plugin-dir loads external drop-in plugins prior to resolution."""

        dropin_dir = tmp_path / "dropin_agent"
        dropin_dir.mkdir()

        code = """from collections.abc import Mapping
from pathlib import Path
from declusor import config, contract, testing

class DropinConfig(contract.ParsedArguments, total=False):
    pass

class DropinPlugin(contract.IPluginExtension[DropinConfig]):
    name = "dropin_agent"
    description = "Dropin agent"
    options_type = DropinConfig
    supported_controllers = frozenset()

    @classmethod
    def configure_parser(cls, parser: contract.IArgumentParser, /) -> None:
        pass

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> DropinConfig:
        return DropinConfig()

    @classmethod
    def build_config(
        cls,
        host: str,
        port: int,
        options: DropinConfig,
        /,
        filesystem: contract.PluginFilesystem | None = None,
        mode: config.ExecutionMode = config.DEFAULT_EXECUTION_MODE,
    ) -> contract.PluginConfig[DropinConfig]:
        dummy_fs = contract.PluginFilesystem(
            root=Path("."),
            assets=Path("."),
            launchers=Path("."),
            modules=Path("."),
            helpers=Path("."),
        )
        return contract.PluginConfig(
            kind=cls.name,
            host=host,
            port=port,
            options=options,
            options_type=cls.options_type,
            filesystem=filesystem or dummy_fs,
            mode=mode,
        )

    @classmethod
    def validate(cls, plugin_config: contract.PluginConfig[DropinConfig], /) -> None:
        pass

    @classmethod
    def build_runtime(cls, plugin_config: contract.PluginConfig[DropinConfig], /) -> contract.IPluginRuntime:
        return testing.DummyPluginRuntime()
"""
        (dropin_dir / "plugin.py").write_text(code, encoding="utf-8")

        manager = core.PluginManager()
        parser = core.DeclusorParser(name="test_app")

        plugin_config = parser.parse(
            manager,
            ["127.0.0.1", "9000", "--plugin-dir", str(tmp_path), "-p", "dropin_agent"],
        )

        assert plugin_config.kind == "dropin_agent"
        assert "dropin_agent" in manager.names()
        assert manager.get_source("dropin_agent") == "cli-plugin-dir:dropin_agent"

    def test_parse_positional_only__rejects_keyword_arguments(self) -> None:
        """The parse method enforces positional-only manager and argv arguments."""

        manager = core.PluginManager()
        parser = core.DeclusorParser(name="test_app")

        with pytest.raises(TypeError, match="positional-only"):
            parser.parse(manager=manager, argv=["127.0.0.1", "9000"])  # type: ignore[call-arg]

    def test_parse__custom_plugin_arguments__configures_parser_and_extracts_options(self) -> None:
        """Plugins dynamically register custom CLI flags via configure_parser, received in options."""

        class CustomPluginConfig(contract.ParsedArguments, total=False):
            banner: str

        class CustomArgPlugin(contract.IPluginExtension[CustomPluginConfig]):
            name = "custom_arg_plugin"
            description = "Plugin registering custom CLI arguments"
            options_type = CustomPluginConfig
            supported_controllers = frozenset()

            @classmethod
            def configure_parser(cls, parser: contract.IArgumentParser, /) -> None:
                parser.add_argument("--banner", default="default_banner")

            @classmethod
            def extract_options(cls, raw: Mapping[str, object], /) -> CustomPluginConfig:
                return CustomPluginConfig(banner=str(raw.get("banner", "default_banner")))

            @classmethod
            def build_config(
                cls,
                host: str,
                port: int,
                options: CustomPluginConfig,
                /,
                filesystem: contract.PluginFilesystem | None = None,
                mode: config.ExecutionMode = config.DEFAULT_EXECUTION_MODE,
            ) -> contract.PluginConfig[CustomPluginConfig]:
                dummy_fs = contract.PluginFilesystem(
                    root=Path("."),
                    assets=Path("."),
                    launchers=Path("."),
                    modules=Path("."),
                    helpers=Path("."),
                )
                return contract.PluginConfig(
                    kind=cls.name,
                    host=host,
                    port=port,
                    options=options,
                    options_type=cls.options_type,
                    filesystem=filesystem or dummy_fs,
                    mode=mode,
                )

            @classmethod
            def validate(cls, plugin_config: contract.PluginConfig[CustomPluginConfig], /) -> None:
                pass

            @classmethod
            def build_runtime(cls, plugin_config: contract.PluginConfig[CustomPluginConfig], /) -> contract.IPluginRuntime:
                return testing.DummyPluginRuntime()

        manager = core.PluginManager()
        manager.register(CustomArgPlugin)

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(
            manager,
            ["127.0.0.1", "9000", "-p", "custom_arg_plugin", "--banner", "custom_banner_value"],
        )

        assert plugin_config.options.get("banner") == "custom_banner_value"

    def test_parse__plugin_validation_failure__propagates_plugin_validation_error(self) -> None:
        """When Plugin.validate raises an exception, parser.parse propagates it."""

        testing.DummyPlugin.reset()
        testing.DummyPlugin.validation_error = config.PluginValidationError("Plugin configuration invalid.")
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")

        with pytest.raises(config.PluginValidationError, match="Plugin configuration invalid"):
            parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name])

    def test_parse__empty_host__raises_parser_error(self) -> None:
        """Passing an empty host string via CLI raises ParserError."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)
        parser = core.DeclusorParser(name="test_app")

        with pytest.raises(config.ParserError, match="invalid Host value"):
            parser.parse(manager, ["", "9000", "-p", testing.DummyPlugin.name])

    def test_parse__negative_port__raises_parser_error(self) -> None:
        """Passing a negative port via CLI raises ParserError."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)
        parser = core.DeclusorParser(name="test_app")

        with pytest.raises(config.ParserError, match="invalid Port value"):
            parser.parse(manager, ["127.0.0.1", "-1", "-p", testing.DummyPlugin.name])

    def test_parse__out_of_range_port__raises_parser_error(self) -> None:
        """Passing a port exceeding 65535 via CLI raises ParserError."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)
        parser = core.DeclusorParser(name="test_app")

        with pytest.raises(config.ParserError, match="invalid Port value"):
            parser.parse(manager, ["127.0.0.1", "70000", "-p", testing.DummyPlugin.name])

    def test_parse__missing_all_positional_arguments__raises_parser_error(self) -> None:
        """Omitting both host and port positional arguments raises ParserError."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)
        parser = core.DeclusorParser(name="test_app")

        with pytest.raises(config.ParserError):
            parser.parse(manager, [])


class TestDeclusorParserPluginResolution:
    """Tests verifying plugin resolution and selection logic in DeclusorParser."""

    def test_resolve_plugin__explicit_flag__resolves_specified_plugin(self) -> None:
        """Specifying -p or --plugin selects that registered plugin."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name])

        assert plugin_config.kind == testing.DummyPlugin.name

    def test_resolve_plugin__omitted_flag__defaults_to_shell_socket_or_first_registered(self) -> None:
        """When --plugin is omitted, the parser defaults to DEFAULT_DECLUSOR_PLUGIN or first available."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(manager, ["127.0.0.1", "9000"])

        assert plugin_config.kind == testing.DummyPlugin.name

    def test_resolve_plugin__unregistered_plugin_name__raises_parser_error_with_choices(self) -> None:
        """Requesting an unregistered plugin name raises ParserError listing available choices."""

        manager = core.PluginManager()
        parser = core.DeclusorParser(name="test_app")

        with pytest.raises(config.ParserError, match="invalid choice: 'nonexistent'"):
            parser.parse(manager, ["127.0.0.1", "9000", "-p", "nonexistent"])

    def test_resolve_plugin__empty_plugin_manager__raises_parser_error_no_client_available(self) -> None:
        """When no plugins are registered in the manager, ParserError is raised."""

        manager = core.PluginManager()
        parser = core.DeclusorParser(name="test_app")

        with pytest.raises(config.ParserError, match="No client plugin available"):
            parser.parse(manager, ["127.0.0.1", "9000"])

    def test_resolve_plugin__non_string_plugin_attribute__raises_parser_error(self) -> None:
        """If preliminary parsed plugin argument is not a string, ParserError is raised."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        class NonStringPluginParser(core.DeclusorParser):
            def parse_known_args(  # type: ignore[override]
                self,
                args: object = None,
                namespace: object = None,
            ) -> tuple[object, list[str]]:
                fake_args = type("Args", (), {"plugin_dir": None, "plugin": 12345})()
                return fake_args, []

        parser = NonStringPluginParser(name="test_app")

        with pytest.raises(config.ParserError, match="argument -p/--plugin: expected string, got int"):
            parser.parse(manager, ["127.0.0.1", "9000"])

    def test_resolve_plugin__prefers_default_declusor_plugin_over_alphabetically_earlier_plugin(self) -> None:
        """When --plugin is omitted, DEFAULT_DECLUSOR_PLUGIN is preferred over earlier alphabetical choices."""

        class AlphaPlugin(testing.DummyPlugin):
            name = "alpha_plugin"

        class ShellPlugin(testing.DummyPlugin):
            name = config.DEFAULT_DECLUSOR_PLUGIN.value

        manager = core.PluginManager()
        manager.register(AlphaPlugin)
        manager.register(ShellPlugin)

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(manager, ["127.0.0.1", "9000"])

        assert plugin_config.kind == config.DEFAULT_DECLUSOR_PLUGIN.value

    def test_resolve_plugin__falls_back_to_alphabetically_first_when_default_not_registered(self) -> None:
        """When DEFAULT_DECLUSOR_PLUGIN is not among available plugins, falls back to first available."""

        class FirstPlugin(testing.DummyPlugin):
            name = "aaa_plugin"

        class SecondPlugin(testing.DummyPlugin):
            name = "zzz_plugin"

        manager = core.PluginManager()
        manager.register(SecondPlugin)
        manager.register(FirstPlugin)

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(manager, ["127.0.0.1", "9000"])

        assert plugin_config.kind == "aaa_plugin"


class TestDeclusorParserExecutionMode:
    """Tests verifying execution mode parsing in DeclusorParser."""

    def test_parse__default_mode__is_cli(self) -> None:
        """Default execution mode is ExecutionMode.CLI."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name])

        assert plugin_config.mode == config.ExecutionMode.CLI

    def test_parse__explicit_mode_long_flag__sets_execution_mode(self) -> None:
        """Specifying --mode http sets ExecutionMode.HTTP."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(
            manager,
            ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "--mode", "http"],
        )

        assert plugin_config.mode == config.ExecutionMode.HTTP

    def test_parse__explicit_mode_short_flag__sets_execution_mode(self) -> None:
        """Specifying -m mcp sets ExecutionMode.MCP."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(
            manager,
            ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "-m", "mcp"],
        )

        assert plugin_config.mode == config.ExecutionMode.MCP

    def test_parse__invalid_mode__raises_parser_error(self) -> None:
        """Providing an invalid execution mode raises ParserError."""

        manager = core.PluginManager()
        parser = core.DeclusorParser(name="test_app")

        with pytest.raises(config.ParserError):
            parser.parse(manager, ["127.0.0.1", "9000", "--mode", "unsupported_mode"])


class TestDeclusorParserLauncherOutput:
    """Tests verifying launcher output configuration parsing in DeclusorParser."""

    def test_parse__default_launcher_output__is_terminal_with_none_path(self) -> None:
        """Default launcher output mode is TERMINAL with None path."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name])

        assert plugin_config.launcher_output_mode == config.LauncherOutputMode.TERMINAL
        assert plugin_config.launcher_output_path is None

    def test_parse__explicit_silent_output__sets_silent_mode(self) -> None:
        """Specifying --launcher-output silent sets SILENT mode."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(
            manager,
            ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "--launcher-output", "silent"],
        )

        assert plugin_config.launcher_output_mode == config.LauncherOutputMode.SILENT
        assert plugin_config.launcher_output_path is None

    def test_parse__explicit_file_output__sets_file_mode_and_path(self, tmp_path: Path) -> None:
        """Specifying --launcher-output file:<path> sets FILE mode and destination Path."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        out_path = tmp_path / "client.sh"
        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(
            manager,
            ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "--launcher-output", f"file:{out_path}"],
        )

        assert plugin_config.launcher_output_mode == config.LauncherOutputMode.FILE
        assert plugin_config.launcher_output_path == out_path

    def test_parse__invalid_launcher_output__raises_parser_error(self) -> None:
        """Providing an unsupported launcher output choice raises ParserError."""

        manager = core.PluginManager()
        parser = core.DeclusorParser(name="test_app")

        with pytest.raises(config.ParserError, match="--launcher-output"):
            parser.parse(manager, ["127.0.0.1", "9000", "--launcher-output", "unsupported"])

    def test_parse__file_launcher_output_empty_path__raises_parser_error(self) -> None:
        """Specifying --launcher-output file: with no destination raises ParserError."""

        manager = core.PluginManager()
        parser = core.DeclusorParser(name="test_app")

        with pytest.raises(config.ParserError, match="--launcher-output"):
            parser.parse(manager, ["127.0.0.1", "9000", "--launcher-output", "file:"])


class TestDeclusorParserLauncherWrapper:
    """Tests verifying launcher wrapper template parsing in DeclusorParser."""

    def test_parse__default_launcher_wrapper__is_none(self) -> None:
        """Default launcher wrapper is None."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name])

        assert plugin_config.launcher_wrapper is None

    @pytest.mark.skip(reason="--launcher-wrapper CLI option is temporarily disabled as a future feature")
    def test_parse__explicit_launcher_wrapper__sets_wrapper_template(self) -> None:
        """Specifying --launcher-wrapper populates launcher_wrapper in config."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(
            manager,
            [
                "127.0.0.1",
                "9000",
                "-p",
                testing.DummyPlugin.name,
                "--launcher-wrapper",
                "python3 -c '$DECLUSOR_SCRIPT'",
            ],
        )

        assert plugin_config.launcher_wrapper == "python3 -c '$DECLUSOR_SCRIPT'"

    @pytest.mark.skip(reason="--launcher-wrapper CLI option is temporarily disabled as a future feature")
    def test_parse__empty_launcher_wrapper__raises_parser_error(self) -> None:
        """Passing an empty string for --launcher-wrapper raises ParserError."""

        manager = core.PluginManager()
        parser = core.DeclusorParser(name="test_app")

        with pytest.raises(config.ParserError, match="--launcher-wrapper"):
            parser.parse(manager, ["127.0.0.1", "9000", "--launcher-wrapper", ""])


class TestDeclusorParserTimeout:
    """Tests verifying timeout option parsing in DeclusorParser."""

    def test_parse__default_timeout__is_none(self) -> None:
        """Default socket timeout is None."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name])

        assert plugin_config.timeout is None

    def test_parse__explicit_timeout_short_flag__sets_timeout_float(self) -> None:
        """Specifying -t with numeric string sets float timeout."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(
            manager,
            ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "-t", "5.5"],
        )

        assert plugin_config.timeout == 5.5

    def test_parse__explicit_timeout_long_flag__sets_timeout_float(self) -> None:
        """Specifying --timeout with integer sets float timeout."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(
            manager,
            ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "--timeout", "10"],
        )

        assert plugin_config.timeout == 10.0

    def test_parse__negative_timeout__raises_parser_error(self) -> None:
        """Passing a negative timeout raises ParserError."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")

        with pytest.raises(config.ParserError, match="invalid Timeout value"):
            parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "-t", "-1.0"])

    def test_parse__invalid_timeout_type__raises_parser_error(self) -> None:
        """Passing a non-numeric string for timeout raises ParserError."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")

        with pytest.raises(config.ParserError):
            parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "-t", "not_a_number"])


class TestDeclusorParserTransportLayers:
    """Tests verifying repeatable transport layer option parsing in DeclusorParser."""

    def test_parse__default_transport_layers__is_empty_tuple(self) -> None:
        """Default transport_layers is an empty tuple."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(manager, ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name])

        assert plugin_config.transport_layers == ()

    def test_parse__single_transport_layer__records_layer_in_tuple(self) -> None:
        """Single --transport-layer flag populates a single-element tuple."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(
            manager,
            ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "--transport-layer", "xor"],
        )

        assert plugin_config.transport_layers == ("xor",)

    def test_parse__multiple_transport_layers__preserves_sequence_order(self) -> None:
        """Repeatable --transport-layer flags accumulate in order."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(
            manager,
            [
                "127.0.0.1",
                "9000",
                "-p",
                testing.DummyPlugin.name,
                "--transport-layer",
                "xor",
                "--transport-layer",
                "xor",
            ],
        )

        assert plugin_config.transport_layers == ("xor", "xor")

    def test_parse__invalid_transport_layer__raises_parser_error_with_choices(self) -> None:
        """Supplying an unknown transport layer raises ParserError listing valid options."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        parser = core.DeclusorParser(name="test_app")

        with pytest.raises(config.ParserError, match="invalid choice: 'unknown'"):
            parser.parse(
                manager,
                ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "--transport-layer", "unknown"],
            )

    def test_parse__custom_transport_registry__validates_against_injected_registry(self) -> None:
        """Parser validates transport layers against custom injected TransportLayerRegistry."""

        testing.DummyPlugin.reset()
        manager = core.PluginManager()
        manager.register(testing.DummyPlugin)

        custom_registry = transport.TransportLayerRegistry()

        class CustomLayer(contract.ITransportLayer):
            def __init__(self, transport: contract.ITransport) -> None:
                self._transport = transport

            @property
            def underlying(self) -> contract.ITransport:
                return self._transport

            def read(self, buffer_size: int = 1024, /) -> bytes:
                return b""

            def write(self, data: bytes, /) -> None:
                pass

            def close(self) -> None:
                pass

        custom_registry.register("custom", lambda transport: CustomLayer(transport))

        parser = core.DeclusorParser(name="test_app")
        plugin_config = parser.parse(
            manager,
            ["127.0.0.1", "9000", "-p", testing.DummyPlugin.name, "--transport-layer", "custom"],
            transport_registry=custom_registry,
        )

        assert plugin_config.transport_layers == ("custom",)
