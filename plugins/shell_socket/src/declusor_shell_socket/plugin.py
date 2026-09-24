from pathlib import Path
from socket import socket

from declusor import config, contract, util

from .connection import ShellSocketConnection, ShellSocketFileStore, ShellSocketProfile

_REPO_ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"
_PACKAGE_ASSETS_DIR = Path(__file__).resolve().parent / "assets"
ASSETS_DIR = _REPO_ASSETS_DIR if _REPO_ASSETS_DIR.exists() else _PACKAGE_ASSETS_DIR


class ShellSocketPlugin(contract.IClientPlugin):
    """Plugin that configures the traditional shell-over-socket client.

    Deploys a Bash payload that connects to Declusor over TCP using Linux's
    built-in /dev/tcp virtual devices, requiring no external binaries on the target.
    """

    name = "shell_socket"
    """Unique identifier for the shell-socket client."""

    description = "Bash-based reverse shell using Linux /dev/tcp pseudo-devices."
    """Brief human-readable description for CLI help."""

    version = "1.0.0"
    """Plugin version."""

    author = "Declusor Team"
    """Plugin author."""

    default_assets_dir = ASSETS_DIR
    """Path to bundled assets."""

    @classmethod
    def configure_parser(cls, parser: util.Parser, /) -> None:
        """Register shell_socket-specific command-line arguments."""

        return None

    @classmethod
    def build_config(cls, args: util.Namespace, data_paths: config.DataPaths | None = None, /) -> contract.ClientConfig:
        """Build the shell_socket client configuration."""

        if data_paths is not None:
            client_data = data_paths.for_client(cls.name)
            launcher_path = client_data.launcher / "shell_socket_client.sh"
            helpers_dir = client_data.helpers
            modules_dir = client_data.modules
        else:
            launcher_path = ASSETS_DIR / "launchers" / "shell_socket_client.sh"
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
        """Validate the shell_socket client configuration."""

        launcher_path = client_config.options.get("launcher_path")

        if not isinstance(launcher_path, Path):
            raise config.ParserError("Invalid shell_socket launcher path.")

        launcher_path = launcher_path.resolve()

        if not launcher_path.is_file():
            raise config.ParserError(f"Client launcher file does not exist: {launcher_path}")

    @classmethod
    def build_runtime(cls, client_config: contract.ClientConfig, /) -> contract.IClientRuntime:
        """Build the shell_socket runtime from client configuration."""

        return ShellSocketRuntime(client_config)


class ShellSocketRuntime(contract.IClientRuntime):
    """Runtime adapter between shell_socket configuration and its transport."""

    def __init__(self, client_config: contract.ClientConfig, /) -> None:
        self._client_config = client_config

        self._profile = ShellSocketProfile(
            name=client_config.kind,
            ack_server_raw=config.Settings.DEFAULT_SERVER_ACK,
            ack_client_raw=util.hash_sha256(config.Settings.DEFAULT_CLIENT_ACK_SEED),
        )

        launcher_path: Path = client_config.options.get("launcher_path") or (ASSETS_DIR / "launchers" / "shell_socket_client.sh")
        helpers_dir: Path = client_config.options.get("helpers_dir") or (ASSETS_DIR / "helpers")
        modules_dir: Path = client_config.options.get("modules_dir") or (ASSETS_DIR / "modules")

        self._files = ShellSocketFileStore(
            launcher_path,
            helpers_dir,
            modules_dir,
            library_extensions=(".sh",),
            module_extensions=(".sh",),
        )

    @property
    def client_files(self) -> contract.IClientFileStore:
        """The shell_socket file store."""

        return self._files

    @property
    def client_script(self) -> str:
        """Return the rendered client bootstrap script."""

        return self._files.render_client_script(
            self._client_config.host,
            self._client_config.port,
            self._profile.ack_client_raw,
        )

    def create_connection(self, connection: socket, /) -> contract.IConnection:
        """Create a shell_socket connection for an accepted socket."""

        return ShellSocketConnection(connection, self._profile, self._files)
