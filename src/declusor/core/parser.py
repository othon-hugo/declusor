from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Final

from declusor import config, contract, util

if TYPE_CHECKING:
    from declusor.core.plugin import PluginManager


class DeclusorParser(util.Parser):
    """Parser for command-line arguments."""

    flags: Final[dict[str, str]] = {
        "host": "IP address or hostname where the service should run",
        "port": "port number to listen on for incoming connections",
        "plugin": "agent responsible for handling requests",
        "assets_dir": "root directory containing client launchers, helpers, and modules",
        "plugin_dir": "additional directory to discover custom drop-in plugins",
        "mode": "application execution mode (choices: %(choices)s)",
    }

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
            "host",
            help=self.flags["host"],
            type=str,
        )

        self.add_argument(
            "port",
            help=self.flags["port"],
            type=int,
        )

        self.add_argument(
            "--assets-dir",
            help=self.flags["assets_dir"],
            type=Path,
            default=None,
        )

        self.add_argument(
            "--plugin-dir",
            help=self.flags["plugin_dir"],
            type=Path,
            default=None,
        )

        self.add_argument(
            "-p",
            "--plugin",
            help=self.flags["plugin"],
            type=str,
            default=None,
        )

        self.add_argument(
            "-m",
            "--mode",
            help=self.flags["mode"],
            type=config.ExecutionMode.from_string,
            choices=list(config.ExecutionMode),
            default=config.Settings.DEFAULT_EXECUTION_MODE,
        )

        self._is_configured = True

    def parse(
        self,
        manager: "PluginManager",
        argv: Sequence[str] | None = None,
        /,
    ) -> contract.PluginConfig[contract.ParsedArguments]:
        """Parse arguments and build a validated PluginConfig using the provided manager.

        Args:
            manager: Plugin manager containing the client plugins available to the application.
            argv: Sequence of arguments to parse, excluding the program name.

        Returns:
            Validated PluginConfig populated from command-line arguments.

        Raises:
            ParserError: If required arguments are missing, values are invalid, or no plugin matches.
        """

        preliminary_args, _ = self.parse_known_args(argv)

        plugin_dir = getattr(preliminary_args, "plugin_dir", None)

        if plugin_dir:
            manager.load_from_directory(plugin_dir, source_label="cli-plugin-dir", allow_override=True)

        available_clients = manager.names()
        default_client = "shell_socket" if "shell_socket" in available_clients else (available_clients[0] if available_clients else None)
        plugin_name = preliminary_args.plugin or default_client

        if not plugin_name:
            raise config.ParserError("No client plugin available.")

        if plugin_name not in available_clients:
            raise config.ParserError(
                f"argument -p/--plugin: invalid choice: '{plugin_name}' (choose from {', '.join(repr(c) for c in available_clients)})"
            )

        Plugin = manager.get(plugin_name)
        Plugin.configure_parser(self)

        raw_args = self.parse_args(argv)
        raw_dict: dict[str, object] = vars(raw_args)

        host_raw = raw_dict.get("host")

        if not isinstance(host_raw, str):
            raise config.ParserError("Missing or invalid 'host' argument.")

        host = host_raw
        port_raw = raw_dict.get("port")

        if not isinstance(port_raw, int):
            raise config.ParserError("Missing or invalid 'port' argument.")

        port = port_raw
        mode_raw = raw_dict.get("mode")
        mode = mode_raw if isinstance(mode_raw, config.ExecutionMode) else config.Settings.DEFAULT_EXECUTION_MODE

        assets_dir_raw = raw_dict.get("assets_dir")
        assets_dir = assets_dir_raw if isinstance(assets_dir_raw, Path) else None
        filesystem = contract.PluginFilesystem.from_root(assets_dir) if assets_dir is not None else None

        plugin_raw: Mapping[str, object] = {k: v for k, v in raw_dict.items() if k not in self.flags}
        options = Plugin.extract_options(plugin_raw)

        plugin_config = Plugin.build_config(host, port, options, filesystem=filesystem, mode=mode)
        Plugin.validate(plugin_config)

        return plugin_config
