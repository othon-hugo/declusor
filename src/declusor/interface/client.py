from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from declusor import util


@dataclass(frozen=True)
class ClientConfig:
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

    options: dict[str, Any] = field(default_factory=dict)
    """Client-specific configuration options."""


class IClientPlugin(ABC):
    """Extension point for registering configurable client implementations.

    Implementations define how their command-line arguments are registered,
    converted into a ``ClientConfig``, and validated.
    """

    name: str
    """Unique identifier used to select the client from the command line."""

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
    def build_config(cls, args: util.Namespace, /) -> ClientConfig:
        """Build a client configuration from parsed arguments.

        Args:
            args: Namespace containing common and client-specific arguments.

        Returns:
            Configuration object for the selected client.
        """

        raise NotImplementedError

    @classmethod
    @abstractmethod
    def validate(cls, client_config: ClientConfig, /) -> None:
        """Validate a client configuration.

        Args:
            client_config: Configuration produced by ``build_config``.

        Raises:
            config.ParserError: If the configuration is invalid.
        """

        raise NotImplementedError
