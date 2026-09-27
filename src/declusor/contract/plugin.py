from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from declusor import config

if TYPE_CHECKING:
    from declusor.contract.connection import IConnection
    from declusor.contract.parser import IArgumentParser, ParsedArguments
    from declusor.contract.transport import ITransport


@dataclass(frozen=True)
class PluginConfig[T: ParsedArguments]:
    """Configuration produced by a client plugin.

    Stores the common server connection parameters and the client-specific
    options produced during command-line parsing.
    """

    kind: str
    """Registered identifier of the client implementation."""

    host: str
    """Host address used by the server."""

    port: int
    """Port used by the server."""

    options: T
    """Client-specific configuration options, typed to the plugin's TypedDict."""

    options_type: type[T]
    """The concrete TypedDict class for this plugin's parsed options.

    Retained alongside ``options`` so that callers can perform runtime
    isinstance checks (e.g. ``isinstance(config.options, config.options_type)``)
    without resorting to ``Any``.
    """

    filesystem: "PluginFilesystem"
    """Filesystem paths used by the selected client runtime."""

    mode: config.ExecutionMode = config.Settings.DEFAULT_EXECUTION_MODE
    """Application execution mode (e.g. CLI, API, MCP, HTTP)."""


@dataclass(frozen=True)
class PluginFilesystem:
    """Filesystem paths used by a plugin runtime."""

    root: Path
    """Root directory containing the plugin directories."""

    assets: Path
    """Root directory for plugin asset files."""

    launchers: Path
    """Directory containing client bootstrap templates and launcher scripts."""

    modules: Path
    """Directory containing payload modules."""

    helpers: Path
    """Directory containing reusable client helper libraries."""

    @classmethod
    def from_root(cls, root: Path, /) -> "PluginFilesystem":
        """Build normalized filesystem paths from a root directory.

        If ``root/assets`` exists it is used as the assets directory; otherwise
        ``root`` itself is treated as the assets directory so that both
        installed packages (assets bundled inside the package) and repository
        layouts (assets in a sibling ``assets/`` directory) work without extra
        configuration.

        Args:
            root: Base directory for the plugin.

        Returns:
            Immutable ``PluginFilesystem`` derived from ``root``.
        """

        normalized_root = root.expanduser().resolve()

        if (normalized_root / "assets").is_dir():
            assets = normalized_root / "assets"
        elif normalized_root.is_dir():
            assets = normalized_root
        else:
            raise config.PluginValidationError(f"Plugin assets directory not found at: {normalized_root}")

        return cls(
            root=normalized_root,
            assets=assets,
            launchers=assets / "launchers",
            modules=assets / "modules",
            helpers=assets / "helpers",
        )


class IPluginExtension[T: ParsedArguments](ABC):
    """Extension point for registering configurable client implementations.

    Each autonomous plugin subclasses ``ParsedArguments`` to declare its own
    typed options (e.g. ``ShellSocketConfig``), then subclasses
    ``IPluginExtension[ShellSocketConfig]`` and provides concrete
    implementations for all abstract methods.

    The parser never constructs the plugin's TypedDict directly.  Instead it
    calls ``configure_parser`` (so the plugin can register its flags) and then
    ``extract_options`` (so the plugin converts the raw namespace dict into its
    own statically typed ``T``).  This keeps ``Any`` entirely out of the
    parse-to-config pipeline.
    """

    name: str
    """Unique identifier used to select the client from the command line."""

    description: str = ""
    """Brief human-readable description shown in CLI help."""

    version: str = "1.0.0"
    """Semantic version of the client plugin."""

    author: str = ""
    """Author or maintainer of the client plugin."""

    options_type: type[T]
    """The concrete TypedDict class for this plugin's parsed options."""

    @classmethod
    @abstractmethod
    def configure_parser(cls, parser: "IArgumentParser", /) -> None:
        """Register client-specific command-line arguments.

        Args:
            parser: Argument parser that receives the client-specific options.
        """

        raise NotImplementedError

    @classmethod
    @abstractmethod
    def extract_options(cls, raw: Mapping[str, object], /) -> T:
        """Construct plugin-specific typed options from the parsed namespace dict.

        Called by the application parser after it has stripped all standard
        keys (``host``, ``port``, ``plugin``, ``mode``, ``assets_dir``,
        ``plugin_dir``).  The remaining key-value pairs correspond to the
        arguments registered by ``configure_parser`` and are passed here as a
        plain ``Mapping[str, object]``.

        The plugin is the sole authority on converting this mapping into its
        own statically typed ``T`` — no ``Any`` is required at the call site.

        Args:
            raw: Residual argument mapping after common keys have been removed.

        Returns:
            A fully typed instance of ``T``.
        """

        raise NotImplementedError

    @classmethod
    @abstractmethod
    def validate(cls, plugin_config: "PluginConfig[T]", /) -> None:
        """Validate a client configuration.

        Args:
            plugin_config: Configuration produced by ``build_config``.

        Raises:
            config.ParserError: If the configuration is invalid.
        """

        raise NotImplementedError

    @classmethod
    @abstractmethod
    def build_config(
        cls,
        host: str,
        port: int,
        options: T,
        /,
        filesystem: "PluginFilesystem | None" = None,
        mode: config.ExecutionMode = config.Settings.DEFAULT_EXECUTION_MODE,
    ) -> "PluginConfig[T]":
        """Build a client configuration from typed options and filesystem paths.

        Args:
            host: Host address the server will bind to.
            port: Port the server will listen on.
            options: Plugin-specific options produced by ``extract_options``.
            filesystem: Resolved filesystem paths, or ``None`` to fall back to
                the plugin's own bundled assets.
            mode: Application execution mode.

        Returns:
            Immutable configuration object for the selected client.
        """

        raise NotImplementedError

    @classmethod
    @abstractmethod
    def build_runtime(cls, plugin_config: "PluginConfig[T]", /) -> "IPluginRuntime":
        """Build the runtime for a validated client configuration.

        Args:
            plugin_config: Configuration produced by ``build_config``.

        Returns:
            Runtime that can render the bootstrap script and create connections.
        """

        raise NotImplementedError


class IPluginRuntime(ABC):
    """Runtime used by the service to operate a configured client.

    A runtime hides client-specific bootstrap and connection construction from
    the application service.
    """

    @property
    @abstractmethod
    def processor(self) -> "IPluginProcessor":
        """Client file store for module and library loading."""

        raise NotImplementedError

    @property
    @abstractmethod
    def launcher(self) -> str:
        """Return the rendered client bootstrap script."""

        raise NotImplementedError

    @abstractmethod
    def create_connection(self, transport: "ITransport", /) -> "IConnection":
        """Create a connection for an accepted transport channel.

        Args:
            transport: Accepted transport connected to the remote client.

        Returns:
            Connection implementation for the configured client.
        """

        raise NotImplementedError


class IPluginProcessor(ABC):
    """File-access interface for plugin-specific assets.

    Provides the application layer with a transport-agnostic handle to load
    launcher scripts, helper libraries, and on-demand modules without knowing
    the concrete filesystem layout of each plugin.
    """

    @property
    @abstractmethod
    def helpers(self, /) -> bytes:
        """[...]"""

        raise NotImplementedError

    @abstractmethod
    def load_module(self, module: str, /) -> bytes:
        """Load an on-demand payload module by name.

        Args:
            module: Module file name relative to the modules directory.

        Returns:
            Raw bytes of the module file.
        """

        raise NotImplementedError

    @abstractmethod
    def load_helper(self, helper: str, /) -> bytes:
        """Load a single helper library by name.

        Args:
            helper: Helper file name relative to the helpers directory.

        Returns:
            Raw bytes of the helper file.
        """

        raise NotImplementedError

    @abstractmethod
    def load_all_helpers(self) -> Mapping[str, bytes]:
        """Load all available helper libraries.

        Returns:
            Mapping of helper file names to their raw bytes.
        """

        raise NotImplementedError

    @abstractmethod
    def render_launcher(self, host: str, port: int, acknowledge: bytes, /) -> bytes:
        """Read and render the client bootstrap script.

        Args:
            host: Host address embedded in the client script.
            port: Port embedded in the client script.
            acknowledge: Client acknowledgment bytes embedded in the script.

        Returns:
            The rendered client bootstrap script as bytes.
        """

        raise NotImplementedError
