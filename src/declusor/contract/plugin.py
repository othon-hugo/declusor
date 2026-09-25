from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from socket import socket
from typing import TYPE_CHECKING, Any

from declusor import util
from declusor.config import DataPaths

if TYPE_CHECKING:
    from declusor.contract.connection import IConnection


@dataclass(frozen=True)
class PluginConfig:
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

    data_paths: DataPaths | None = None
    """Optional filesystem paths used by the selected client runtime."""

    options: dict[str, Any] = field(default_factory=dict)
    """Client-specific configuration options."""


class IPluginRuntime(ABC):
    """Runtime used by the service to operate a configured client.

    A runtime hides client-specific bootstrap and connection construction from
    the application service.
    """

    @property
    @abstractmethod
    def client_files(self) -> "IClientFileStore":
        """[...]"""

        raise NotImplementedError

    @property
    @abstractmethod
    def client_script(self) -> str:
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


class IPlugin(ABC):
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
    def configure_parser(cls, parser: util.Parser, /) -> None:
        """Register client-specific command-line arguments.

        Args:
            parser: Argument parser that receives the client-specific options.
        """

        raise NotImplementedError

    @classmethod
    @abstractmethod
    def build_config(cls, args: util.Namespace, data_paths: DataPaths | None = None, /) -> PluginConfig:
        """Build a client configuration from parsed arguments and data paths.

        Args:
            args: Namespace containing common and client-specific arguments.
            data_paths: Resolved filesystem paths for the application, or None to use bundled assets.

        Returns:
            Configuration object for the selected client.
        """

        raise NotImplementedError

    @classmethod
    @abstractmethod
    def validate(cls, plugin_config: PluginConfig, /) -> None:
        """Validate a client configuration.

        Args:
            plugin_config: Configuration produced by ``build_config``.

        Raises:
            config.ParserError: If the configuration is invalid.
        """

        raise NotImplementedError

    @classmethod
    @abstractmethod
    def build_runtime(cls, plugin_config: PluginConfig, /) -> IPluginRuntime:
        """Build the runtime for a validated client configuration.

        Args:
            plugin_config: Configuration produced by ``build_config``.

        Returns:
            Runtime that can render the bootstrap and create connections.
        """

        raise NotImplementedError


class IClientFileStore(ABC):
    """Provides client bootstrap, library and module file operations.

    Libraries are loaded automatically during session initialization, while
    modules are loaded only when explicitly requested by the operator.
    """

    @abstractmethod
    def render_client_script(self, host: str, port: int, acknowledge: bytes, /) -> str:
        """Read and render the client bootstrap script.

        Args:
            host: Host address embedded in the client script.
            port: Port embedded in the client script.
            acknowledge: Client acknowledgment bytes embedded in the script.

        Returns:
            The rendered client bootstrap script.
        """

        raise NotImplementedError

    @abstractmethod
    def load_library(self) -> bytes:
        """Load libraries uploaded automatically during initialization.

        Returns:
            Concatenated library contents.
        """

        raise NotImplementedError

    @abstractmethod
    def load_module(self, module_name: str, /) -> bytes:
        """Load one operator-selected module.

        Args:
            module_name: Module filename relative to the modules directory.

        Returns:
            Raw module contents.
        """

        raise NotImplementedError
