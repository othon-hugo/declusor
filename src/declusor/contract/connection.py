from abc import ABC, abstractmethod
from collections.abc import Generator
from enum import StrEnum
from typing import Self

from declusor import config


class ConnectionState(StrEnum):
    """Lifecycle state machine for a client connection.

    States transition deterministically:
    ``CREATED`` -> ``INITIALIZING`` -> ``CONNECTED`` -> ``CLOSED``.
    """

    CREATED = "CREATED"
    """Connection instantiated but protocol handshake not yet initiated."""

    INITIALIZING = "INITIALIZING"
    """Handshake in progress (transmitting helpers and verifying ACK sentinel)."""

    CONNECTED = "CONNECTED"
    """Handshake completed successfully; channel is ready for command operations."""

    CLOSED = "CLOSED"
    """Connection terminated gracefully or due to underlying network failure."""

    @property
    def is_created(self) -> bool:
        """Indicate whether the connection state is CREATED."""

        return self == ConnectionState.CREATED

    @property
    def is_initializing(self) -> bool:
        """Indicate whether the connection state is INITIALIZING."""

        return self == ConnectionState.INITIALIZING

    @property
    def is_connected(self) -> bool:
        """Indicate whether the connection state is CONNECTED."""

        return self == ConnectionState.CONNECTED

    @property
    def is_closed(self) -> bool:
        """Indicate whether the connection state is CLOSED."""

        return self == ConnectionState.CLOSED

    @property
    def can_handshake(self) -> bool:
        """Indicate whether protocol handshake can be initiated in this state."""

        return self == ConnectionState.CREATED

    @property
    def can_perform_io(self) -> bool:
        """Indicate whether read or write operations can be performed in this state."""

        return self in (ConnectionState.CONNECTED, ConnectionState.INITIALIZING)

    def ensure_can_handshake(self) -> None:
        """Assert that this state permits protocol handshake.

        Raises:
            ConnectionError: If connection is closed or already initialized.
        """

        if self.is_closed:
            raise config.ConnectionError("Cannot initialize a closed connection.")

        if not self.can_handshake:
            raise config.ConnectionError("Connection is already initialized.")

    def ensure_can_perform_io(self) -> None:
        """Assert that this state permits write or read operations.

        Raises:
            ConnectionClosed: If connection is closed.
            ConnectionError: If connection is in CREATED state prior to handshake.
        """

        if self.is_closed:
            raise config.ConnectionClosed("Connection is closed.")

        if not self.can_perform_io:
            raise config.ConnectionError("Cannot perform I/O on connection that is not connected.")


class IOperationRenderer(ABC):
    """Command syntax renderer for remote clients.

    Translates abstract OperationCode tokens into agent-specific command
    strings without performing network I/O.
    """

    @abstractmethod
    def render_operation_command(self, opcode: config.OperationCode, /, *args: str) -> str | None:
        """Build the command string for a given operation code.

        Maps an ``OperationCode`` to its client-side function name and appends
        each argument as a shell-quoted token. Returns ``None`` if the opcode
        is not supported by this renderer.

        Args:
            opcode: The operation to invoke on the client.
            *args: Positional string arguments forwarded to the client function.

        Returns:
            A ready-to-send command string, or ``None`` if the opcode is unsupported.
        """

        raise NotImplementedError


class IConnection(ABC):
    """Manages an active network session with a remote client.

    Handles the full lifecycle of a connection: initialization (handshake),
    framed read/write over the transport layer, and graceful shutdown.
    Supports the context manager protocol — ``close()`` is called automatically
    on exit.
    """

    def __init__(self, connection: "IConnection | None" = None, /) -> None:
        self._underlying_connection = connection

    def handshake(self) -> None:
        """Execute protocol handshake to establish an active, authenticated session."""

        if self._underlying_connection:
            self._underlying_connection.handshake()

    @property
    @abstractmethod
    def state(self) -> ConnectionState:
        """Current lifecycle state of the connection."""

        raise NotImplementedError

    @property
    def is_created(self) -> bool:
        """Indicate whether the connection is in the CREATED state."""

        return self.state.is_created

    @property
    def is_initializing(self) -> bool:
        """Indicate whether protocol handshake is currently in progress."""

        return self.state.is_initializing

    @property
    def is_connected(self) -> bool:
        """Indicate whether the connection is in the active CONNECTED state."""

        return self.state.is_connected

    @property
    def is_closed(self) -> bool:
        """Indicate whether the connection has been closed."""

        return self.state.is_closed

    @property
    def can_handshake(self) -> bool:
        """Indicate whether protocol handshake can be performed on the connection."""

        return self.state.can_handshake

    @property
    def can_perform_io(self) -> bool:
        """Indicate whether write and read operations can be performed on the connection."""

        return self.state.can_perform_io

    def ensure_can_handshake(self) -> None:
        """Assert that connection state permits protocol handshake.

        Raises:
            ConnectionError: If connection is closed or already initialized.
        """

        self.state.ensure_can_handshake()

    def ensure_can_perform_io(self) -> None:
        """Assert that connection state permits write or read operations.

        Raises:
            ConnectionClosed: If connection is closed.
            ConnectionError: If connection is in CREATED state prior to handshake.
        """

        self.state.ensure_can_perform_io()

    @property
    @abstractmethod
    def renderer(self) -> IOperationRenderer:
        """The command syntax renderer for this connection."""

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
