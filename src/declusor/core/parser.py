from collections.abc import Sequence
from typing import Final, TypedDict

from declusor import config, interface, util
from declusor.core.clients import ClientRegistry


class DeclusorOptions(TypedDict):
    """Arguments for the application."""

    host: str
    port: int
    client: interface.ClientConfig


class DeclusorParser(util.Parser, interface.IParser[DeclusorOptions]):
    """Parser for command-line arguments."""

    flags: Final[dict[str, str]] = {
        "host": "IP address or hostname where the service should run",
        "port": "port number to listen on for incoming connections",
        "client": "agent responsible for handling requests",
    }

    def __init__(self, registry: ClientRegistry, /, name: str, description: str = "") -> None:
        """Create a parser backed by a specific client registry.

        Args:
            registry: Registry containing the clients available to the application.
            *args: Arguments forwarded to ``argparse.ArgumentParser``.
            **kwargs: Keyword arguments forwarded to ``argparse.ArgumentParser``.
        """

        super().__init__(prog=name, description=description or None)

        self._registry = registry

    def _configure_common_arguments(self) -> None:
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
            "-c",
            "--client",
            help=self.flags["client"],
            type=str,
            choices=self._registry.names(),
            default=str(config.ClientFile.SHELL_SOCKET),
        )

    def parse(self, argv: Sequence[str] | None = None, /) -> DeclusorOptions:
        self._configure_common_arguments()

        preliminary_args, _ = self.parse_known_args(argv)
        plugin = self._registry.get(preliminary_args.client)
        plugin.configure_parser(self)

        args = self.parse_args(argv)

        client_config = plugin.build_config(args)
        plugin.validate(client_config)

        return DeclusorOptions(
            host=args.host,
            port=args.port,
            client=client_config,
        )
