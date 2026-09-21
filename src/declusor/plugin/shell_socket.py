from pathlib import Path
from socket import socket

from declusor import config, contract, util
from declusor import connection as connection_module


class ShellSocketPlugin(contract.IClientPlugin):
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
    def build_config(cls, args: util.Namespace, data_paths: config.DataPaths, /) -> contract.ClientConfig:
        """Build the shell-socket client configuration.

        Args:
            args: Parsed common and client-specific arguments.
            data_paths: Resolved filesystem paths for the application.

        Returns:
            Configuration containing the shell-socket client template path.
        """

        client_path = data_paths.clients / cls.name

        return contract.ClientConfig(
            kind=cls.name,
            host=args.host,
            port=args.port,
            options={
                "client_path": client_path,
            },
            data_paths=data_paths,
        )

    @classmethod
    def validate(cls, client_config: contract.ClientConfig, /) -> None:
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
        clients_directory = client_config.data_paths.clients

        if not util.validate_file_relative(client_path, clients_directory):
            raise config.ParserError(f"Invalid client file: {client_path}")

        if not client_path.is_file():
            raise config.ParserError(f"Client file does not exist: {client_path}")

    @classmethod
    def build_runtime(cls, client_config: contract.ClientConfig, /) -> contract.IClientRuntime:
        """Build the shell-socket runtime from client configuration.

        Args:
            client_config: Validated shell-socket configuration.

        Returns:
            Runtime responsible for rendering and connecting the shell client.
        """

        return ShellSocketRuntime(client_config)


class ShellSocketRuntime(contract.IClientRuntime):
    """Runtime adapter between shell client configuration and its transport."""

    def __init__(self, client_config: contract.ClientConfig, /) -> None:
        self._client_config = client_config

        self._profile = connection_module.ShellSocketProfile(
            name=client_config.kind,
            ack_server_raw=b"\x00",
            ack_client_raw=util.hash_sha256(b"\xba\xdc\x00\xff\xee"),
        )

        self._files = connection_module.ShellSocketFileStore(
            client_config.options["client_path"],
            client_config.data_paths,
            (".sh",),
            (".sh",),
        )

    @property
    def client_files(self) -> contract.IClientFileStore:
        """[...]"""

        return self._files

    @property
    def client_script(self) -> str:
        """Return the rendered shell client bootstrap script."""

        return self._files.render_client_script(
            self._client_config.host,
            self._client_config.port,
            self._profile.ack_client_raw,
        )

    def create_connection(self, connection: socket, /) -> contract.IConnection:
        """Create a shell-socket connection for an accepted socket.

        Args:
            connection: Accepted socket connected to the shell client.

        Returns:
            Shell-socket connection configured with the selected profile.
        """

        return connection_module.ShellSocketConnection(connection, self._profile, self._files)
