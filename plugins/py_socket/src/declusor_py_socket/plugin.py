from collections.abc import Mapping
from pathlib import Path
from socket import socket

from declusor import config, contract, util

from .connection import PySocketConnection, PySocketProfile

_DEFAULT_ROOT = Path(__file__).resolve().parents[2]


class PySocketConfig(contract.ParsedArguments, total=False):
    """Client-specific configuration options for py_socket."""


class PySocketPlugin(contract.IPluginExtension[PySocketConfig]):
    """Plugin that configures the Python reverse-shell client.

    Registers the ``py_socket`` client, which deploys a self-contained Python
    agent compatible with any Python 3.6+ environment. Unlike the shell_socket
    client, this agent operates cross-platform (Linux, macOS, Windows) and
    evaluates payloads natively in the Python runtime via ``exec``, or through
    the operating system shell via ``subprocess``.
    """

    name = "py_socket"
    description = "Cross-platform Python reverse-shell with in-memory execution and subprocess fallback."
    version = "1.0.0"
    author = "Declusor Team"
    options_type = PySocketConfig

    @classmethod
    def configure_parser(cls, parser: contract.IArgumentParser, /) -> None:
        """Register py_socket-specific command-line arguments."""

        return None

    @classmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> PySocketConfig:
        """Extract and construct typed options for py_socket."""

        return PySocketConfig()

    @classmethod
    def build_config(
        cls,
        host: str,
        port: int,
        options: PySocketConfig,
        /,
        filesystem: contract.PluginFilesystem | None = None,
        mode: config.ExecutionMode = config.Settings.DEFAULT_EXECUTION_MODE,
    ) -> contract.PluginConfig[PySocketConfig]:
        """Build the py_socket client configuration."""

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
    def validate(cls, plugin_config: contract.PluginConfig[PySocketConfig], /) -> None:
        """Validate the py_socket client configuration."""

        launcher_file = plugin_config.filesystem.launchers / "py_socket_client.py"

        if not launcher_file.is_file():
            raise config.ParserError(f"Client launcher file does not exist: {launcher_file}")

    @classmethod
    def build_runtime(cls, plugin_config: contract.PluginConfig[PySocketConfig], /) -> contract.IPluginRuntime:
        """Build the py_socket runtime from client configuration."""

        return PySocketRuntime(plugin_config)


class PySocketRuntime(contract.IPluginRuntime):
    """Runtime adapter between Python client configuration and its transport."""

    def __init__(self, plugin_config: contract.PluginConfig[PySocketConfig], /) -> None:
        self._plugin_config = plugin_config

        self._profile = PySocketProfile(
            name=plugin_config.kind,
            ack_server_raw=config.Settings.DEFAULT_SERVER_ACK,
            ack_client_raw=util.hash_sha256(config.Settings.DEFAULT_CLIENT_ACK_SEED),
        )

        self._processor = PySocketProcessor(plugin_config.filesystem)

    @property
    def processor(self) -> contract.IPluginProcessor:
        """The Python client file store."""

        return self._processor

    @property
    def launcher(self) -> str:
        """Return the rendered Python client launcher script."""

        rendered_bytes = self._processor.render_launcher(
            self._plugin_config.host,
            self._plugin_config.port,
            self._profile.ack_client_raw,
        )

        return rendered_bytes.decode("utf-8")

    def create_connection(self, connection: socket, /) -> contract.IConnection:
        """Create a py_socket connection for an accepted socket."""

        return PySocketConnection(connection, self._profile, self._processor)


class PySocketProcessor(contract.IPluginProcessor):
    """Filesystem adapter for Python client templates, libraries and payloads.

    Resolves launchers, helpers and modules from the plugin's own self-contained
    assets directory, with support for user-specified overlay directories.
    """

    def __init__(
        self,
        filesystem: contract.PluginFilesystem,
        library_extensions: tuple[str, ...] = (".py",),
        module_extensions: tuple[str, ...] = (".py",),
    ) -> None:
        self._filesystem = filesystem
        self._library_extensions = library_extensions
        self._module_extensions = module_extensions

    def render_launcher(self, host: str, port: int, acknowledge: bytes, /) -> bytes:
        """Read and render the Python client bootstrap launcher script."""

        launcher_path = self._filesystem.launchers / "py_socket_client.py"

        try:
            client_script_template = launcher_path.read_text(encoding="utf-8")
        except OSError as error:
            raise config.ConnectionError(f"Failed to read client script: {error}") from error

        rendered = util.format_template(
            client_script_template,
            HOST=host,
            PORT=str(port),
            ACKNOWLEDGE=acknowledge.hex(),
        )

        return rendered.encode("utf-8")

    def load_helper(self, helper: str, /) -> bytes:
        """Load a single helper library by name."""

        helper_path = (self._filesystem.helpers / helper).resolve()

        if not util.validate_file_relative(helper_path, self._filesystem.helpers):
            raise config.InvalidOperation(f"Helper path '{helper}' is outside permitted directory.")

        return util.load_file(helper_path)

    def load_all_helpers(self) -> Mapping[str, bytes]:
        """Load all valid Python helper libraries."""

        if not self._filesystem.helpers.exists():
            return {}

        helpers: dict[str, bytes] = {}

        for file in sorted(self._filesystem.helpers.iterdir()):
            if file.is_file() and util.validate_file_extension(file, self._library_extensions):
                helpers[file.name] = util.load_file(file)

        return helpers

    def helpers(self) -> bytes:
        """Load and concatenate valid Python helper libraries for backward compatibility."""

        all_helpers = self.load_all_helpers()

        return b"\n\n".join(all_helpers.values())

    def load_module(self, module: str, /) -> bytes:
        """Load one operator-selected module from the modules directory."""

        module_path = (self._filesystem.modules / module).resolve()

        if not util.validate_file_relative(module_path, self._filesystem.modules):
            raise config.InvalidOperation(f"Module path '{module}' is outside the permitted modules directory.")

        if not util.validate_file_extension(module_path, self._module_extensions):
            raise config.InvalidOperation(f"Module '{module}' has an unsupported extension. Allowed: {self._module_extensions}")

        return util.load_file(module_path)


PySocketFileStore = PySocketProcessor
