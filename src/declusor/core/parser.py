from collections.abc import Sequence
from pathlib import Path
from typing import Final, TypedDict

from declusor import config, contract, util
from declusor.core.plugin import ClientPluginRegistry


class DeclusorOptions(TypedDict):
    """Arguments for the application."""

    host: str
    port: int
    client: contract.ClientConfig


class DeclusorParser(util.Parser, contract.IParser[DeclusorOptions]):
    """Parser for command-line arguments."""

    flags: Final[dict[str, str]] = {
        "host": "IP address or hostname where the service should run",
        "port": "port number to listen on for incoming connections",
        "client": "agent responsible for handling requests",
    }

    def __init__(self, registry: ClientPluginRegistry, /, name: str, description: str = "") -> None:
        """Create a parser backed by a specific client registry.

        Args:
            registry: Registry containing the clients available to the application.
            *args: Arguments forwarded to ``argparse.ArgumentParser``.
            **kwargs: Keyword arguments forwarded to ``argparse.ArgumentParser``.
        """

        super().__init__(prog=name, description=description or None)

        self._registry = registry
        self._configured = False
        self._configure_common_arguments()

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
            help="root directory containing clients, modules and libraries",
            type=Path,
            default=config.BasePath.DATA_DIR,
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
            "-c",
            "--client",
            help=self.flags["client"],
            type=str,
            choices=available_clients if available_clients else None,
            default=default_client,
        )

        self._configured = True

    def parse(self, argv: Sequence[str] | None = None, /) -> DeclusorOptions:
        preliminary_args, _ = self.parse_known_args(argv)

        plugin_dir = getattr(preliminary_args, "plugin_dir", None)
        if plugin_dir and hasattr(self._registry, "load_from_directory"):
            self._registry.load_from_directory(plugin_dir, source_label="cli-plugin-dir", allow_override=True)

        plugin = self._registry.get(preliminary_args.client)
        plugin.configure_parser(self)

        args = self.parse_args(argv)

        data_paths = config.DataPaths.from_root(args.data_root)
        client_config = plugin.build_config(args, data_paths)
        plugin.validate(client_config)

        return DeclusorOptions(
            host=args.host,
            port=args.port,
            client=client_config,
        )
