from typing import TypedDict

from declusor import config, interface, util


class DeclusorOptions(TypedDict):
    """Arguments for the application."""

    host: str
    port: int
    client: config.ClientFile


class DeclusorParser(util.Parser, interface.IParser[DeclusorOptions]):
    """Parser for command-line arguments."""

    info = {
        "host": "IP address or hostname where the service should run",
        "port": "port number to listen on for incoming connections",
        "client": "agent responsible for handling requests",
    }

    def parse(self) -> DeclusorOptions:
        """Parse command-line arguments."""

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
            type=config.ClientFile,
            default=config.ClientFile.SHELL_SOCKET,
        )

        args = self.parse_args()
        declusor_opts = DeclusorOptions(host=args.host, port=args.port, client=args.client)

        self._validate_all_arguments(declusor_opts)

        try:
            return declusor_opts
        except AttributeError as e:
            raise config.ParserError(f"Missing argument: {e.name}") from e

    def _validate_all_arguments(self, declusor_opts: DeclusorOptions) -> None:
        self._validate_client_argument(declusor_opts["client"])

    def _validate_client_argument(self, client_filename: str) -> None:
        client_filepath = (config.BasePath.CLIENTS_DIR / client_filename).resolve()

        if not util.validate_file_relative(client_filepath, config.BasePath.CLIENTS_DIR):
            raise config.ParserError(f"Invalid client file: {client_filepath}")
