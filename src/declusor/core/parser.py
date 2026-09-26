from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Final, TypedDict

from declusor import config, contract, util

if TYPE_CHECKING:
    from declusor.core.plugin import PluginManager


class DeclusorOptions(TypedDict):
    """Arguments for the application."""

    host: str
    port: int
    plugin: contract.PluginConfig


class DeclusorParser(util.Parser, contract.IParser[DeclusorOptions]):
    """Parser for command-line arguments."""

    flags: Final[dict[str, str]] = {
        "host": "IP address or hostname where the service should run",
        "port": "port number to listen on for incoming connections",
        "plugin": "agent responsible for handling requests",
    }

    def __init__(self, manager: "PluginManager", /, name: str, description: str = "") -> None:
        """Create a parser backed by a specific client plugin manager.

        Args:
            manager: Plugin manager containing the clients available to the application.
            name: Program name.
            description: Short description of the application.
        """

        super().__init__(prog=name, description=description or None)

        self._manager = manager
        self._registry = manager
        self._configured = False
        self._configure_common_arguments()

    @property
    def manager(self) -> "PluginManager":
        """The client plugin manager backing this parser."""

        return self._manager

    def _configure_common_arguments(self) -> None:
        if self._configured:
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
            "--data-root",
            help="root directory containing client launchers, helpers, and modules",
            type=Path,
            default=None,
        )

        self.add_argument(
            "--plugin-dir",
            help="additional directory to discover custom drop-in plugins",
            type=Path,
            default=None,
        )

        available_clients = self._registry.names()
        default_client = "shell_socket" if "shell_socket" in available_clients else (available_clients[0] if available_clients else None)

        self.add_argument(
            "-p",
            "--plugin",
            help=self.flags["plugin"],
            type=str,
            choices=available_clients if available_clients else None,
            default=default_client,
        )

        self._configured = True

    def parse(self, argv: Sequence[str] | None = None, /) -> DeclusorOptions:
        preliminary_args, _ = self.parse_known_args(argv)

        plugin_dir = getattr(preliminary_args, "plugin_dir", None)

        if plugin_dir:
            self._manager.load_from_directory(plugin_dir, source_label="cli-plugin-dir", allow_override=True)

        Plugin = self._manager.get(preliminary_args.plugin)
        Plugin.configure_parser(self)

        raw_args = self.parse_args(argv)
        args = contract.PluginNamespace.from_namespace(raw_args)

        data_paths = config.DataPaths.from_root(args.data_root) if args.data_root is not None else None
        plugin_config = Plugin.build_config(args, data_paths)

        Plugin.validate(plugin_config)

        return DeclusorOptions(
            host=args.host,
            port=args.port,
            plugin=plugin_config,
        )
