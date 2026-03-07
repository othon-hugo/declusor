from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generator, Self

if TYPE_CHECKING:
    from declusor.interface import profile


class IConnection(ABC):
    """Manages an active network session with a remote client.

    Handles the full lifecycle of a connection: initialization (handshake),
    framed read/write over the transport layer, and graceful shutdown.
    Supports the context manager protocol — ``close()`` is called automatically
    on exit.
    """

    @property
    @abstractmethod
    def client(self) -> "profile.IProfile":
        """The configuration profile for the connected client.

        Returns:
            The ``IProfile`` instance that was used to open this connection.
        """

        raise NotImplementedError

    @property
    @abstractmethod
    def timeout(self) -> float | None:
        """Socket operation timeout, in seconds.

        Returns:
            Seconds to wait before a socket call times out, or ``None`` for
            no timeout (blocking indefinitely).
        """

        raise NotImplementedError

    @timeout.setter
    @abstractmethod
    def timeout(self, value: float | None, /) -> None:
        """Set the socket operation timeout.

        Args:
            value: Timeout in seconds, or ``None`` to block indefinitely.
        """

        raise NotImplementedError

    @abstractmethod
    def initialize(self) -> None:
        """Perform the initial protocol handshake.

        Typically sends the library payload to the client and verifies the
        client's acknowledgment before the session is considered ready.

        Raises:
            ConnectionFailure: If the handshake times out or the client ACK
                is invalid.
        """

        raise NotImplementedError

    @abstractmethod
    def read(self) -> Generator[bytes, None, None]:
        """Read a framed message from the remote client.

        Yields chunks of data until the client's ACK sentinel is received.
        The sentinel itself is excluded from the yielded data.

        Yields:
            Successive ``bytes`` chunks of the incoming message payload.

        Raises:
            ConnectionFailure: On timeout, connection reset, or other I/O error.
        """

        raise NotImplementedError

    @abstractmethod
    def write(self, content: bytes, /) -> None:
        """Send data to the remote client, followed by the server ACK sentinel.

        Args:
            content: The raw bytes payload to transmit.

        Raises:
            ConnectionFailure: On timeout or I/O error during transmission.
        """

        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Close the underlying transport and release all associated resources."""

        raise NotImplementedError

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object) -> None:
        self.close()
