from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Final

from declusor import config, contract, util

if TYPE_CHECKING:
    from declusor.core.plugin import PluginManager


class DeclusorParser(util.Parser):
    """Parser for command-line arguments."""

    class Host(str):
        """Validated host value parsed from the command line."""

        arg_name: Final = "host"
        arg_help: Final = "IP address or hostname where the service should run"

        def __new__(cls, value: str) -> "DeclusorParser.Host":
            if not value:
                raise ValueError("host cannot be empty")

            return super().__new__(cls, value)

    class Port(int):
        """Validated TCP port parsed from the command line."""

        arg_name: Final = "port"
        arg_help: Final = "port number to listen on for incoming connections"

        def __new__(cls, value: int | str) -> "DeclusorParser.Port":
            port = int(value)

            if not 0 <= port <= 65535:
                raise ValueError("port must be between 0 and 65535")

            return super().__new__(cls, port)

    class Plugin(str):
        """Plugin name parsed from the command line."""

        arg_name: Final = "plugin"
        arg_help: Final = "agent responsible for handling requests"
        arg_flags: Final = ("-p", "--plugin")

        def __new__(cls, value: str) -> "DeclusorParser.Plugin":
            if not value:
                raise ValueError("plugin cannot be empty")

            return super().__new__(cls, value)

    class AssetsDir(Path):
        """Root directory containing application assets."""

        arg_name: Final = "assets_dir"
        arg_help: Final = "root directory containing client launchers, helpers, and modules"
        arg_flags: Final = ("--assets-dir",)

    class PluginDir(Path):
        """Additional directory from which plugins are discovered."""

        arg_name: Final = "plugin_dir"
        arg_help: Final = "additional directory to discover custom drop-in plugins"
        arg_flags: Final = ("--plugin-dir",)

    class ExecutionMode(str):
        """Execution mode argument definition."""

        arg_name: Final = "mode"
        arg_help: Final = "runtime execution mode (e.g. cli, api, mcp, http)"
        arg_flags: Final = ("-m", "--mode")
        arg_choices: Final = tuple(config.ExecutionMode)
        arg_default: Final = config.DEFAULT_EXECUTION_MODE

        def __new__(cls, value: str) -> "DeclusorParser.ExecutionMode":
            if not value:
                raise ValueError("execution mode cannot be empty")

            try:
                mode = config.ExecutionMode.from_string(value)
            except ValueError as error:
                choices = ", ".join(repr(m.value) for m in config.ExecutionMode)
                raise ValueError(f"invalid choice: {value!r} (choose from {choices})") from error

            return super().__new__(cls, mode.value)

    declusor_arguments: Final = (
        Host.arg_name,
        Port.arg_name,
        Plugin.arg_name,
        AssetsDir.arg_name,
        PluginDir.arg_name,
        ExecutionMode.arg_name,
    )

    def __init__(self, name: str, description: str = "") -> None:
        """Create a parser for command-line arguments.

        Args:
            name: Program name.
            description: Short description of the application.
        """

        super().__init__(prog=name, description=description or None)

        self._is_configured = False
        self._configure_common_arguments()

    def _configure_common_arguments(self) -> None:
        if self._is_configured:
            return

        self.add_argument(
            self.Host.arg_name,
            help=self.Host.arg_help,
            type=self.Host,
        )

        self.add_argument(
            self.Port.arg_name,
            help=self.Port.arg_help,
            type=self.Port,
        )

        self.add_argument(
            *self.AssetsDir.arg_flags,
            help=self.AssetsDir.arg_help,
            type=self.AssetsDir,
            default=None,
        )

        self.add_argument(
            *self.PluginDir.arg_flags,
            help=self.PluginDir.arg_help,
            type=self.Plugin,
            default=None,
        )

        self.add_argument(
            *self.Plugin.arg_flags,
            help=self.Plugin.arg_help,
            type=self.Plugin,
            default=None,
        )

        self.add_argument(
            *self.ExecutionMode.arg_flags,
            help=self.ExecutionMode.arg_help,
            choices=self.ExecutionMode.arg_choices,
            default=self.ExecutionMode.arg_default,
            type=self.ExecutionMode,
        )

        self._is_configured = True

    def parse(
        self,
        manager: "PluginManager",
        argv: Sequence[str] | None = None,
        /,
    ) -> contract.PluginConfig[contract.ParsedArguments]:
        """Parse arguments and build a validated plugin configuration.

        Args:
            manager: Plugin manager containing the client plugins available to
                the application.
            argv: Sequence of arguments to parse, excluding the program name.

        Returns:
            Validated plugin configuration populated from command-line arguments.

        Raises:
            config.ParserError: If no plugin is available, the requested plugin
                does not exist, or the resulting configuration is invalid.
        """

        preliminary_args, _ = self.parse_known_args(argv)
        plugin_dir: Path | None = preliminary_args.plugin_dir

        if plugin_dir is not None:
            manager.load_from_directory(
                plugin_dir,
                source_label="cli-plugin-dir",
                allow_override=True,
            )

        available_plugins = manager.names()
        default_plugin = (
            config.DEFAULT_DECLUSOR_PLUGIN.value
            if config.DEFAULT_DECLUSOR_PLUGIN.value in available_plugins
            else (available_plugins[0] if available_plugins else None)
        )
        plugin_name: str | None = preliminary_args.plugin or default_plugin

        if not plugin_name:
            raise config.ParserError("No client plugin available.")

        if plugin_name not in available_plugins:
            choices = ", ".join(repr(name) for name in available_plugins)
            raise config.ParserError(f"argument -p/--plugin: invalid choice: {plugin_name!r} (choose from {choices})")

        Plugin = manager.get(plugin_name)
        Plugin.configure_parser(self)

        args = self.parse_args(argv)

        plugin_options = {key: value for key, value in vars(args).items() if key not in self.declusor_arguments}
        plugin_filesystem = contract.PluginFilesystem.from_root(args.assets_dir) if args.assets_dir is not None else None

        options: contract.ParsedArguments = Plugin.extract_options(plugin_options)

        plugin_config = Plugin.build_config(
            args.host,
            args.port,
            options,
            filesystem=plugin_filesystem,
            mode=config.ExecutionMode(args.mode),
        )

        Plugin.validate(plugin_config)

        return plugin_config
