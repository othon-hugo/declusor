from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from socket import socket
from typing import TYPE_CHECKING

from declusor import config

if TYPE_CHECKING:
    from declusor.contract.connection import IConnection
    from declusor.contract.parser import IArgumentParser, ParsedArguments


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
    """Client-specific configuration options."""

    options_type: type[T]
    """[...]"""

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
    """[...]"""

    launchers: Path
    """Directory containing client bootstrap templates and launcher scripts."""

    modules: Path
    """Directory containing payload modules."""

    helpers: Path
    """Directory containing reusable client helper libraries."""

    @classmethod
    def from_root(cls, root: Path, /) -> "PluginFilesystem":
        """Build normalized data paths from a root directory.

        Args:
            root: Directory containing ``launchers``, ``modules`` and ``helpers``.

        Returns:
            Immutable paths derived from ``root``.
        """

        normalized_root = root.expanduser().resolve()
        assets = normalized_root / "assets"

        return cls(
            root=normalized_root,
            assets=assets,
            launchers=assets / "launchers",
            modules=assets / "modules",
            helpers=assets / "helpers",
        )


class IPluginExtension[T: ParsedArguments](ABC):
    """Extension point for registering configurable client implementations.

    Implementations define how their command-line arguments are registered,
    converted into a ``PluginConfig``, and validated.
    """

    name: str
    """Unique identifier used to select the client from the command line."""

    description: str = ""
    """Brief human-readable description shown in CLI help."""

    version: str = "1.0.0"
    """Semantic version of the client plugin."""

    author: str = ""
    """Author or maintainer of the client plugin."""

    @classmethod
    @abstractmethod
    def validate(cls, plugin_config: PluginConfig[T], /) -> None:
        """Validate a client configuration.

        Args:
            plugin_config: Configuration produced by ``build_config``.

        Raises:
            config.ParserError: If the configuration is invalid.
        """

        raise NotImplementedError

    @classmethod
    @abstractmethod
    def configure_parser(cls, parser: "IArgumentParser[T]", /) -> None:
        """Register client-specific command-line arguments.

        Args:
            parser: Argument parser that receives the client-specific options.
        """

        raise NotImplementedError

    @classmethod
    @abstractmethod
    def build_config(cls, args: T, filesystem: PluginFilesystem | None = None, /) -> PluginConfig[T]:
        """Build a client configuration from parsed arguments and data paths.

        Args:
            args: Pre-configured namespace or protocol containing common and client-specific arguments.
            data_paths: Resolved filesystem paths for the application, or None to use bundled assets.

        Returns:
            Configuration object for the selected client.
        """

        raise NotImplementedError

    @classmethod
    @abstractmethod
    def build_runtime(cls, plugin_config: PluginConfig[T], /) -> "IPluginRuntime":
        """Build the runtime for a validated client configuration.

        Args:
            plugin_config: Configuration produced by ``build_config``.

        Returns:
            Runtime that can render the bootstrap and create connections.
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
    def create_connection(self, connection: socket, /) -> "IConnection":
        """Create a connection for an accepted socket.

        Args:
            connection: Accepted socket connected to the remote client.

        Returns:
            Connection implementation for the configured client.
        """

        raise NotImplementedError


class IPluginProcessor(ABC):
    """[...]"""

    @abstractmethod
    def load_module(self, module: str, /) -> bytes:
        """[...]"""

        raise NotImplementedError

    @abstractmethod
    def load_helper(self, helper: str, /) -> bytes:
        """[...]"""

        raise NotImplementedError

    @abstractmethod
    def load_all_helpers(self) -> Mapping[str, bytes]:
        """[...]"""

        raise NotImplementedError

    @abstractmethod
    def render_launcher(self, host: str, port: int, acknowledge: bytes, /) -> bytes:
        """Read and render the client bootstrap script.

        Args:
            host: Host address embedded in the client script.
            port: Port embedded in the client script.
            acknowledge: Client acknowledgment bytes embedded in the script.

        Returns:
            The rendered client bootstrap script.
        """

        raise NotImplementedError

    # @abstractmethod
    # def render_variable_assignment(self, name: str, value: str) -> bytes: ...

    # @abstractmethod
    # def render_macro_assignment(self, name: str, routine: str) -> bytes: ...
