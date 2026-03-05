from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generator

if TYPE_CHECKING:
    from declusor.interface import profile


class IConnection(ABC):
    """Abstract base class defining the session interface.

    Sessions manage network connections with clients, handling data
    transmission and timeout configuration.
    """

    @property
    @abstractmethod
    def client(self) -> "profile.IProfile":
        """Returns the client associated with this session.

        Returns:
            An instance of IClient representing the connected client.
        """

        raise NotImplementedError

    @property
    @abstractmethod
    def timeout(self) -> float | None:
        """Timeout for socket operations.

        Returns:
            Float value representing the timeout in seconds, or None if no timeout is set.
        """

        raise NotImplementedError

    @timeout.setter
    @abstractmethod
    def timeout(self, value: float | None, /) -> None:
        """Set the session timeout.

        Args:
            value: Timeout duration in seconds.
        """

        raise NotImplementedError

    @abstractmethod
    def initialize(self) -> None:
        """Perform initial handshake/setup.

        Args:
            library: Binary data representing the library to load.
        """

        raise NotImplementedError

    @abstractmethod
    def read(self) -> Generator[bytes, None, None]:
        """Read data from the session.

        Returns:
            Generator yielding bytes received from the session.
        """

        raise NotImplementedError

    @abstractmethod
    def write(self, content: bytes, /) -> None:
        """Write data to the session.

        Args:
            content: Binary data to send to the session.
        """

        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Close the session stream."""

        raise NotImplementedError
