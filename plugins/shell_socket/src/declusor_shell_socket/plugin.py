from collections.abc import Mapping
from pathlib import Path

from declusor import config, contract, util

from .connection import ShellSocketConnection, ShellSocketProfile

_DEFAULT_ROOT = Path(__file__).resolve().parents[2]


class ShellSocketConfig(contract.ParsedArguments, total=False):
    """Client-specific configuration options for shell_socket."""


class ShellSocketPlugin(contract.IPluginExtension[ShellSocketConfig]):
    """Plugin that configures the traditional shell-over-socket client.

    Deploys a Bash payload that connects to Declusor over TCP using Linux's
    built-in /dev/tcp virtual devices, requiring no external binaries on the target.
    """

    name = "shell_socket"
    description = "Bash-based reverse shell using Linux /dev/tcp pseudo-devices."
    version = "1.0.0"
    author = "github.com/othonhugo"
    options_type = ShellSocketConfig

    @classmethod
    def configure_parser(cls, parser: contract.IArgumentParser, /) -> None:
        """Register shell_socket-specific command-line arguments."""

        return None

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> ShellSocketConfig:
        """Extract and construct typed options for shell_socket."""

        return ShellSocketConfig()

    @classmethod
    def build_config(
        cls,
        host: str,
        port: int,
        options: ShellSocketConfig,
        /,
        filesystem: contract.PluginFilesystem | None = None,
        mode: config.ExecutionMode = config.Settings.DEFAULT_EXECUTION_MODE,
    ) -> contract.PluginConfig[ShellSocketConfig]:
        """Build the shell_socket client configuration."""

        resolved_filesystem = filesystem or contract.PluginFilesystem.from_root(_DEFAULT_ROOT)

        return contract.PluginConfig(
            kind=cls.name,
            host=host,
            port=port,
            options=options,
            options_type=cls.options_type,
            filesystem=resolved_filesystem,
            mode=mode,
        )

    @classmethod
    def validate(cls, plugin_config: contract.PluginConfig[ShellSocketConfig], /) -> None:
        """Validate the shell_socket client configuration."""

        launcher_file = plugin_config.filesystem.launchers / "shell_socket_client.sh"

        if not launcher_file.is_file():
            raise config.ParserError(f"Client launcher file does not exist: {launcher_file}")

    @classmethod
    def build_runtime(cls, plugin_config: contract.PluginConfig[ShellSocketConfig], /) -> contract.IPluginRuntime:
        """Build the shell_socket runtime from client configuration."""

        return ShellSocketRuntime(plugin_config)


class ShellSocketRuntime(contract.IPluginRuntime):
    """Runtime adapter between shell_socket configuration and its transport."""

    def __init__(self, plugin_config: contract.PluginConfig[ShellSocketConfig], /) -> None:
        self._plugin_config = plugin_config

        self._profile = ShellSocketProfile(
            name=plugin_config.kind,
            ack_server_raw=config.Settings.DEFAULT_SERVER_ACK,
            ack_client_raw=util.hash_sha256(config.Settings.DEFAULT_CLIENT_ACK_SEED),
        )

        self._processor = ShellSocketProcessor(plugin_config.filesystem)

    @property
    def processor(self) -> contract.IPluginProcessor:
        """The shell_socket file store."""

        return self._processor

    @property
    def launcher(self) -> str:
        """Return the rendered client bootstrap script."""

        rendered_bytes = self._processor.render_launcher(
            self._plugin_config.host,
            self._plugin_config.port,
            self._profile.ack_client_raw,
        )

        return rendered_bytes.decode("utf-8")

    def create_connection(self, transport: contract.ITransport, /) -> contract.IConnection:
        """Create a shell_socket connection for an accepted transport channel."""

        return ShellSocketConnection(transport, self._profile, self._processor)


class ShellSocketProcessor(contract.IPluginProcessor):
    """Filesystem adapter for shell client templates, libraries and payloads.

    Resolves launchers, helpers and modules from the plugin's own self-contained
    assets directory, with support for user-specified overlay directories.
    """

    def __init__(
        self,
        filesystem: contract.PluginFilesystem,
        library_extensions: tuple[str, ...] = (".sh",),
        module_extensions: tuple[str, ...] = (".sh",),
    ) -> None:
        self._filesystem = filesystem
        self._library_extensions = library_extensions
        self._module_extensions = module_extensions

    @property
    def helpers(self) -> bytes:
        """Load and concatenate valid helper libraries for backward compatibility."""

        all_helpers = self.load_all_helpers()

        return b"\n".join(all_helpers.values())

    def render_launcher(self, host: str, port: int, acknowledge: bytes, /) -> bytes:
        """Read and render the client bootstrap script.

        Args:
            host: Host address embedded in the client script.
            port: Port embedded in the client script.
            acknowledge: Client acknowledgment bytes embedded in the script.

        Returns:
            The rendered client bootstrap script as bytes.
        """

        launcher_path = self._filesystem.launchers / "shell_socket_client.sh"

        try:
            client_script_template = launcher_path.read_text(encoding="utf-8")
        except OSError as error:
            raise config.ConnectionError(f"Failed to read client script: {error}") from error

        hex_ack = util.convert_bytes_to_hex(acknowledge)

        rendered = util.format_template(
            client_script_template,
            DECLUSOR_HOST=host,
            DECLUSOR_PORT=str(port),
            DECLUSOR_ACKNOWLEDGE=hex_ack,
        )

        return rendered.encode("utf-8")

    def load_helper(self, helper: str, /) -> bytes:
        """Load a single helper library by name."""

        helper_path = (self._filesystem.helpers / helper).resolve()

        if not util.validate_file_relative(helper_path, self._filesystem.helpers):
            raise config.InvalidOperation(f"Helper path '{helper}' is outside permitted directory.")

        return util.load_file(helper_path)

    def load_all_helpers(self) -> Mapping[str, bytes]:
        """Load all valid shell helper libraries."""

        if not self._filesystem.helpers.exists():
            return {}

        helpers: dict[str, bytes] = {}

        for file in sorted(self._filesystem.helpers.iterdir()):
            if file.is_file() and util.validate_file_extension(file, self._library_extensions):
                helpers[file.name] = util.load_file(file)

        return helpers

    def load_module(self, module: str, /) -> bytes:
        """Load one operator-selected module from the modules directory."""

        module_path = (self._filesystem.modules / module).resolve()

        if not util.validate_file_relative(module_path, self._filesystem.modules):
            raise config.InvalidOperation(f"Module path '{module}' is outside the permitted modules directory.")

        if not util.validate_file_extension(module_path, self._module_extensions):
            raise config.InvalidOperation(f"Module '{module}' has an unsupported extension. Allowed: {self._module_extensions}")

        return util.load_file(module_path)
