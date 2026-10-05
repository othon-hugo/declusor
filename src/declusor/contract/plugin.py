from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from declusor import config, util

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

    mode: config.ExecutionMode = config.DEFAULT_EXECUTION_MODE
    """Application execution mode (e.g. CLI, API, MCP, HTTP)."""

    timeout: float | None = None
    """Default network socket operation timeout in seconds."""

    launcher_output_mode: config.LauncherOutputMode = config.DEFAULT_LAUNCHER_OUTPUT_MODE
    """Delivery mode for the generated client launcher."""

    launcher_output_path: Path | None = None
    """Destination file path when launcher_output_mode is FILE."""

    launcher_wrapper: str | None = None
    """Optional shell invocation wrapper template."""

    transport_layers: tuple[str, ...] = ()
    """Ordered sequence of transport layer names to wrap around accepted transports."""


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

    supported_controllers: frozenset[config.ControllerType]
    """Application controllers available for this plugin's runtime."""

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
        mode: config.ExecutionMode = config.DEFAULT_EXECUTION_MODE,
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


@dataclass(frozen=True)
class LauncherDelivery:
    """Immutable delivery envelope for a rendered client launcher.

    Carries the raw launcher payload alongside operator-controlled delivery
    options. Encoding support is reserved for a future iteration.
    """

    script: bytes
    """Raw launcher payload produced by the plugin."""

    output_mode: config.LauncherOutputMode = config.DEFAULT_LAUNCHER_OUTPUT_MODE
    """How the launcher is delivered to the operator."""

    output_path: Path | None = None
    """Destination file path; required when output_mode is FILE."""

    wrapper_template: str | None = None
    """Optional shell invocation wrapper using $-based template syntax.

    '$DECLUSOR_SCRIPT' (or '${DECLUSOR_SCRIPT}') is substituted with the rendered payload
    via util.format_template (string.Template.safe_substitute).
    Example: "python3 -c '$DECLUSOR_SCRIPT'"

    Note: when encoding is implemented in a future iteration, the wrapper
    will receive the already-encoded payload. Plugin authors must declare
    a wrapper+encoding pair that is mutually compatible.
    """

    def __post_init__(self) -> None:
        """Validate delivery envelope invariants."""

        if self.output_mode is config.LauncherOutputMode.FILE and self.output_path is None:
            raise config.LauncherDeliveryError("output_path must be set when output_mode is FILE.")

        if self.output_path is not None and self.output_mode is not config.LauncherOutputMode.FILE:
            raise config.LauncherDeliveryError("output_path is only valid when output_mode is FILE.", output_path=self.output_path)

    @property
    def text(self) -> str:
        """Decode raw script bytes to UTF-8 text."""

        return self.script.decode("utf-8")

    @property
    def wrapped_text(self) -> str:
        """Return the script formatted with wrapper_template, or raw text if no wrapper is set."""

        if self.wrapper_template is None:
            return self.text

        return util.format_template(self.wrapper_template, DECLUSOR_SCRIPT=self.text)

    def __str__(self) -> str:
        """Return the decoded script text or wrapped command for string formatting and CLI output."""

        return self.wrapped_text


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
    def launcher(self) -> LauncherDelivery:
        """Return the rendered client bootstrap delivery envelope."""

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
    def filesystem(self) -> PluginFilesystem:
        """Plugin filesystem layout exposing launcher, helper, and module asset directories."""

        raise NotImplementedError

    @property
    @abstractmethod
    def helpers(self) -> bytes:
        """Concatenated bootstrap helper libraries sent to the client during handshake."""

        raise NotImplementedError

    @abstractmethod
    def find_module(self, module_name: str, /) -> Path | None:
        """Resolve a module by name within the plugin's module repository.

        Args:
            module_name: Module identifier or relative path to resolve.

        Returns:
            Resolved Path to the candidate module file if found, None otherwise.
        """

        raise NotImplementedError

    @abstractmethod
    def find_helper(self, helper_name: str, /) -> Path | None:
        """Resolve a helper library by name within the plugin's helper repository.

        Args:
            helper_name: Helper library identifier or relative path to resolve.

        Returns:
            Resolved Path to the helper file if found, None otherwise.
        """

        raise NotImplementedError

    @abstractmethod
    def load_module(self, module_path: Path, /) -> bytes:
        """Read and return raw bytes from a validated module path.

        Args:
            module_path: Validated path to the target module file.

        Returns:
            Raw binary content of the module file.
        """

        raise NotImplementedError

    @abstractmethod
    def load_helper(self, helper_path: Path, /) -> bytes:
        """Read and return raw bytes from a validated helper library path.

        Args:
            helper_path: Validated path to the target helper file.

        Returns:
            Raw binary content of the helper library file.
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
