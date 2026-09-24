from pathlib import Path
from socket import socket

from declusor import config, contract, util
from declusor import connection as connection_module


class PySocketPlugin(contract.IClientPlugin):
    """Plugin that configures the Python reverse-shell client.

    Registers the ``py_socket`` client, which deploys a self-contained Python
    agent compatible with any Python 3.6+ environment. Unlike the shell_socket
    client, this agent operates cross-platform (Linux, macOS, Windows) and
    evaluates payloads natively in the Python runtime via ``exec``, or through
    the operating system shell via ``subprocess``.
    """

    name = "py_socket"
    """Registered identifier of the Python-socket client."""

    @classmethod
    def configure_parser(cls, parser: util.Parser, /) -> None:
        """Register py_socket-specific command-line arguments.

        Args:
            parser: Parser that receives client-specific arguments.
        """

        # The default py_socket client currently has no extra arguments.
        return None

    @classmethod
    def build_config(cls, args: util.Namespace, data_paths: config.DataPaths, /) -> contract.ClientConfig:
        """Build the py_socket client configuration.

        Args:
            args: Parsed common and client-specific arguments.
            data_paths: Resolved filesystem paths for the application.

        Returns:
            Configuration containing the py_socket launcher path.
        """

        client_data = data_paths.for_client(cls.name)
        client_path = client_data.launcher / "py_socket_client.py"

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
        """Validate the py_socket client configuration.

        Args:
            client_config: Configuration produced by ``build_config``.

        Raises:
            config.ParserError: If the launcher script is outside the launchers
                directory or does not exist.
        """

        client_path = client_config.options["client_path"]

        if not isinstance(client_path, Path):
            raise config.ParserError("Invalid py_socket client path.")

        client_path = client_path.resolve()
        launcher_dir = client_config.data_paths.for_client(cls.name).launcher

        if not util.validate_file_relative(client_path, launcher_dir):
            raise config.ParserError(f"Invalid client file: {client_path}")

        if not client_path.is_file():
            raise config.ParserError(f"Client file does not exist: {client_path}")

    @classmethod
    def build_runtime(cls, client_config: contract.ClientConfig, /) -> contract.IClientRuntime:
        """Build the py_socket runtime from client configuration.

        Args:
            client_config: Validated py_socket configuration.

        Returns:
            Runtime responsible for rendering and connecting the Python client.
        """

        return PySocketRuntime(client_config)


class PySocketRuntime(contract.IClientRuntime):
    """Runtime adapter between Python client configuration and its transport.

    Renders the launcher bootstrap script and creates ``PySocketConnection``
    instances for accepted sockets.
    """

    def __init__(self, client_config: contract.ClientConfig, /) -> None:
        self._client_config = client_config

        self._profile = connection_module.PySocketProfile(
            name=client_config.kind,
            ack_server_raw=config.Settings.DEFAULT_SERVER_ACK,
            ack_client_raw=util.hash_sha256(config.Settings.DEFAULT_CLIENT_ACK_SEED),
        )

        self._files = connection_module.PySocketFileStore(
            client_config.options["client_path"],
            client_config.data_paths,
            (".py",),
            (".py",),
        )

    @property
    def client_files(self) -> contract.IClientFileStore:
        """The Python client file store."""

        return self._files

    @property
    def client_script(self) -> str:
        """Return the rendered Python client launcher script."""

        return self._files.render_client_script(
            self._client_config.host,
            self._client_config.port,
            self._profile.ack_client_raw,
        )

    def create_connection(self, connection: socket, /) -> contract.IConnection:
        """Create a py_socket connection for an accepted socket.

        Args:
            connection: Accepted socket connected to the Python client.

        Returns:
            PySocketConnection configured with the selected profile.
        """

        return connection_module.PySocketConnection(connection, self._profile, self._files)
