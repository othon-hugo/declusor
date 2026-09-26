from pathlib import Path
from socket import socket

from declusor import config, contract, util

from .connection import ShellSocketConnection, ShellSocketProfile

_REPO_ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"
_PACKAGE_ASSETS_DIR = Path(__file__).resolve().parent / "assets"
ASSETS_DIR = _REPO_ASSETS_DIR if _REPO_ASSETS_DIR.exists() else _PACKAGE_ASSETS_DIR


class ShellSocketPlugin(contract.IPlugin):
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
    def configure_parser(cls, parser: contract.IArgumentParser, /) -> None:
        """Register shell_socket-specific command-line arguments."""

        return None

    @classmethod
    def build_config(cls, args: contract.PluginArguments, data_paths: config.DataPaths | None = None, /) -> contract.PluginConfig:
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

        return contract.PluginConfig(
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
    def validate(cls, plugin_config: contract.PluginConfig, /) -> None:
        """Validate the shell_socket client configuration."""

        launcher_path = plugin_config.options.get("launcher_path")

        if not isinstance(launcher_path, Path):
            raise config.ParserError("Invalid shell_socket launcher path.")

        launcher_path = launcher_path.resolve()

        if not launcher_path.is_file():
            raise config.ParserError(f"Client launcher file does not exist: {launcher_path}")

    @classmethod
    def build_runtime(cls, plugin_config: contract.PluginConfig, /) -> contract.IPluginRuntime:
        """Build the shell_socket runtime from client configuration."""

        return ShellSocketRuntime(plugin_config)


class ShellSocketRuntime(contract.IPluginRuntime):
    """Runtime adapter between shell_socket configuration and its transport."""

    def __init__(self, plugin_config: contract.PluginConfig, /) -> None:
        self._plugin_config = plugin_config

        self._profile = ShellSocketProfile(
            name=plugin_config.kind,
            ack_server_raw=config.Settings.DEFAULT_SERVER_ACK,
            ack_client_raw=util.hash_sha256(config.Settings.DEFAULT_CLIENT_ACK_SEED),
        )

        launcher_path: Path = plugin_config.options.get("launcher_path") or (ASSETS_DIR / "launchers" / "shell_socket_client.sh")
        helpers_dir: Path = plugin_config.options.get("helpers_dir") or (ASSETS_DIR / "helpers")
        modules_dir: Path = plugin_config.options.get("modules_dir") or (ASSETS_DIR / "modules")

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
            self._plugin_config.host,
            self._plugin_config.port,
            self._profile.ack_client_raw,
        )

    def create_connection(self, connection: socket, /) -> contract.IConnection:
        """Create a shell_socket connection for an accepted socket."""

        return ShellSocketConnection(connection, self._profile, self._files)


class ShellSocketFileStore(contract.IClientFileStore):
    """Filesystem adapter for shell client templates, libraries and payloads.

    Resolves launchers, helpers and modules from the plugin's own self-contained
    assets directory, with support for user-specified overlay directories.
    """

    def __init__(
        self,
        launcher_path: Path,
        helpers_dir: Path,
        modules_dir: Path,
        library_extensions: tuple[str, ...] = (".sh",),
        module_extensions: tuple[str, ...] = (".sh",),
    ) -> None:
        self._launcher_path = launcher_path
        self._helpers_dir = helpers_dir
        self._modules_dir = modules_dir
        self._library_extensions = library_extensions
        self._module_extensions = module_extensions

    def render_client_script(self, host: str, port: int, acknowledge: bytes, /) -> str:
        """Read and render the client bootstrap script."""

        try:
            client_script_template = self._launcher_path.read_text(encoding="utf-8")
        except OSError as error:
            raise config.ConnectionError(f"Failed to read client script: {error}") from error

        hex_ack = util.convert_bytes_to_hex(acknowledge)

        return util.format_template(
            client_script_template,
            DECLUSOR_HOST=host,
            DECLUSOR_PORT=str(port),
            DECLUSOR_ACKNOWLEDGE=hex_ack,
        )

    def load_library(self) -> bytes:
        """Load and concatenate valid helper libraries."""

        if not self._helpers_dir.exists():
            return b""

        modules: list[bytes] = []

        for file in sorted(self._helpers_dir.iterdir()):
            if not file.is_file() or not util.validate_file_extension(file, self._library_extensions):
                continue

            try:
                module_content = util.load_file(file)
            except config.InvalidOperation as error:
                raise config.ConnectionError(f"Failed to read library file: {file}: {error}") from error

            if module_content:
                modules.append(module_content)

        return b"\n".join(modules)

    def load_module(self, module_name: str, /) -> bytes:
        """Load one operator-selected module from the modules directory."""

        module_path = (self._modules_dir / module_name).resolve()

        if not util.validate_file_relative(module_path, self._modules_dir):
            raise config.InvalidOperation(f"Module path '{module_name}' is outside the permitted modules directory.")

        if not util.validate_file_extension(module_path, self._module_extensions):
            raise config.InvalidOperation(f"Module '{module_name}' has an unsupported extension. Allowed: {self._module_extensions}")

        return util.load_file(module_path)
