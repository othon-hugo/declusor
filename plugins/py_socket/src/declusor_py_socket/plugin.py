from pathlib import Path
from socket import socket

from declusor import config, contract, util

from .connection import PySocketConnection, PySocketFileStore, PySocketProfile

_REPO_ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"
_PACKAGE_ASSETS_DIR = Path(__file__).resolve().parent / "assets"
ASSETS_DIR = _REPO_ASSETS_DIR if _REPO_ASSETS_DIR.exists() else _PACKAGE_ASSETS_DIR


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

    description = "Cross-platform Python reverse-shell with in-memory execution and subprocess fallback."
    """Brief human-readable description for CLI help."""

    version = "1.0.0"
    """Plugin version."""

    author = "Declusor Team"
    """Plugin author."""

    default_assets_dir = ASSETS_DIR
    """Path to bundled assets."""

    @classmethod
    def configure_parser(cls, parser: util.Parser, /) -> None:
        """Register py_socket-specific command-line arguments."""

        return None

    @classmethod
    def build_config(cls, args: util.Namespace, data_paths: config.DataPaths | None = None, /) -> contract.ClientConfig:
        """Build the py_socket client configuration."""

        if data_paths is not None:
            client_data = data_paths.for_client(cls.name)
            launcher_path = client_data.launcher / "py_socket_client.py"
            helpers_dir = client_data.helpers
            modules_dir = client_data.modules
        else:
            launcher_path = ASSETS_DIR / "launchers" / "py_socket_client.py"
            helpers_dir = ASSETS_DIR / "helpers"
            modules_dir = ASSETS_DIR / "modules"

        return contract.ClientConfig(
            kind=cls.name,
            host=args.host,
            port=args.port,
            options={
                "launcher_path": launcher_path,
                "helpers_dir": helpers_dir,
                "modules_dir": modules_dir,
            },
            data_paths=data_paths,
        )

    @classmethod
    def validate(cls, client_config: contract.ClientConfig, /) -> None:
        """Validate the py_socket client configuration."""

        launcher_path = client_config.options.get("launcher_path")

        if not isinstance(launcher_path, Path):
            raise config.ParserError("Invalid py_socket launcher path.")

        launcher_path = launcher_path.resolve()

        if not launcher_path.is_file():
            raise config.ParserError(f"Client launcher file does not exist: {launcher_path}")

    @classmethod
    def build_runtime(cls, client_config: contract.ClientConfig, /) -> contract.IClientRuntime:
        """Build the py_socket runtime from client configuration."""

        return PySocketRuntime(client_config)


class PySocketRuntime(contract.IClientRuntime):
    """Runtime adapter between Python client configuration and its transport."""

    def __init__(self, client_config: contract.ClientConfig, /) -> None:
        self._client_config = client_config

        self._profile = PySocketProfile(
            name=client_config.kind,
            ack_server_raw=config.Settings.DEFAULT_SERVER_ACK,
            ack_client_raw=util.hash_sha256(config.Settings.DEFAULT_CLIENT_ACK_SEED),
        )

        launcher_path: Path = client_config.options.get("launcher_path") or (ASSETS_DIR / "launchers" / "py_socket_client.py")
        helpers_dir: Path = client_config.options.get("helpers_dir") or (ASSETS_DIR / "helpers")
        modules_dir: Path = client_config.options.get("modules_dir") or (ASSETS_DIR / "modules")

        self._files = PySocketFileStore(
            launcher_path,
            helpers_dir,
            modules_dir,
            library_extensions=(".py",),
            module_extensions=(".py",),
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
        """Create a py_socket connection for an accepted socket."""

        return PySocketConnection(connection, self._profile, self._files)
