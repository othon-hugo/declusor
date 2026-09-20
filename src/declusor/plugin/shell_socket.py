from pathlib import Path

from declusor import config, interface, util


class ShellSocketPlugin(interface.IClientPlugin):
    """Plugin that configures the shell-socket client."""

    name = str(config.ClientFile.SHELL_SOCKET)
    """Registered identifier of the shell-socket client."""

    @classmethod
    def configure_parser(cls, parser: util.Parser, /) -> None:
        """Register shell-socket-specific command-line arguments.

        Args:
            parser: Parser that receives client-specific arguments.
        """

        # The default shell-socket client currently has no extra arguments.
        return None

    @classmethod
    def build_config(cls, args: util.Namespace, /) -> interface.ClientConfig:
        """Build the shell-socket client configuration.

        Args:
            args: Parsed common and client-specific arguments.

        Returns:
            Configuration containing the shell-socket client template path.
        """

        client_path = config.BasePath.CLIENTS_DIR / cls.name

        return interface.ClientConfig(
            kind=cls.name,
            host=args.host,
            port=args.port,
            options={
                "client_path": client_path,
            },
        )

    @classmethod
    def validate(
        cls,
        client_config: interface.ClientConfig,
        /,
    ) -> None:
        """Validate the shell-socket client configuration.

        Args:
            client_config: Configuration produced by ``build_config``.

        Raises:
            config.ParserError: If the client template is outside the configured
                clients directory or does not exist.
        """

        client_path = client_config.options["client_path"]

        if not isinstance(client_path, Path):
            raise config.ParserError("Invalid shell-socket client path.")

        client_path = client_path.resolve()
        clients_directory = config.BasePath.CLIENTS_DIR.resolve()

        if not util.validate_file_relative(client_path, clients_directory):
            raise config.ParserError(f"Invalid client file: {client_path}")

        if not client_path.is_file():
            raise config.ParserError(f"Client file does not exist: {client_path}")
