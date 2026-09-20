from typing import TypedDict

from declusor import config, interface, util
from declusor.core.clients import ClientRegistry


class DeclusorOptions(TypedDict):
    """Arguments for the application."""

    host: str
    port: int
    client: interface.ClientConfig


class DeclusorParser(util.Parser, interface.IParser[DeclusorOptions]):
    """Parser for command-line arguments."""

    info = {
        "host": "IP address or hostname where the service should run",
        "port": "port number to listen on for incoming connections",
        "client": "agent responsible for handling requests",
    }

    def _configure_common_arguments(self) -> None:
        self.add_argument(
            "host",
            help=self.info["host"],
            type=str,
        )

        self.add_argument(
            "port",
            help=self.info["port"],
            type=int,
        )

        self.add_argument(
            "-c",
            "--client",
            help=self.info["client"],
            type=str,
            choices=ClientRegistry.names(),
            default=str(config.ClientFile.SHELL_SOCKET),
        )

    def parse(self) -> DeclusorOptions:
        self._configure_common_arguments()

        preliminary_args, _ = self.parse_known_args()
        plugin = ClientRegistry.get(preliminary_args.client)
        plugin.configure_parser(self)

        args = self.parse_args()

        client_config = plugin.build_config(args)
        plugin.validate(client_config)

        return DeclusorOptions(
            host=args.host,
            port=args.port,
            client=client_config,
        )
