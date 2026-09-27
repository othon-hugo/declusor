from pathlib import Path
from socket import socket

from declusor import config, contract


class ShellSocketConfig(contract.ParsedArguments):
    """[...]"""


class ShellSocketPlugin[T: ShellSocketConfig](contract.IPluginExtension[T]):
    """Plugin that configures the traditional shell-over-socket client.

    Deploys a Bash payload that connects to Declusor over TCP using Linux's
    built-in /dev/tcp virtual devices, requiring no external binaries on the target.
    """

    name = "shell_socket"
    description = "Bash-based reverse shell using Linux /dev/tcp pseudo-devices."
    version = "0.1.0"
    author = "github.com/othonhugo"

    @classmethod
    def configure_parser(cls, parser: contract.IArgumentParser[T], /) -> None:
        """Register shell_socket-specific command-line arguments."""

        return None

    @classmethod
    def build_config(cls, args: T, filesystem: contract.PluginFilesystem | None = None, /) -> contract.PluginConfig[T]:
        """Build the shell_socket client configuration."""

        raise NotImplementedError

    @classmethod
    def validate(cls, plugin_config: contract.PluginConfig[T], /) -> None:
        """Validate the shell_socket client configuration."""

        launcher_path = plugin_config.options.get("launcher_path")

        if not isinstance(launcher_path, Path):
            raise config.ParserError("Invalid shell_socket launcher path.")

        launcher_path = launcher_path.resolve()

        if not launcher_path.is_file():
            raise config.ParserError(f"Client launcher file does not exist: {launcher_path}")

    @classmethod
    def build_runtime(cls, plugin_config: contract.PluginConfig[T], /) -> contract.IPluginRuntime:
        """Build the shell_socket runtime from client configuration."""

        return ShellSocketRuntime(plugin_config)


class ShellSocketRuntime[T: ShellSocketConfig](contract.IPluginRuntime):
    """Runtime adapter between shell_socket configuration and its transport."""

    def __init__(self, plugin_config: contract.PluginConfig[T], /) -> None:
        raise NotImplementedError

    @property
    def processor(self) -> contract.IPluginProcessor:
        """The shell_socket file store."""

        raise NotImplementedError

    @property
    def launcher(self) -> str:
        """Return the rendered client bootstrap script."""

        raise NotImplementedError

    def create_connection(self, connection: socket, /) -> contract.IConnection:
        """Create a shell_socket connection for an accepted socket."""

        raise NotImplementedError


class ShellSocketProcessor[T: ShellSocketConfig](contract.IPluginProcessor):
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

        raise NotImplementedError
