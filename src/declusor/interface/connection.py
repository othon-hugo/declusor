from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generator, Self

if TYPE_CHECKING:
    from pathlib import Path

    from declusor.config import OperationCode


class IConnectionProfile(ABC):
    """Immutable configuration profile for a remote client.

    Holds protocol parameters (buffer sizes, timeouts, ACK values, supported
    operations) and performs only pure string formatting. All I/O is
    delegated to the ``IConnection`` implementation.
    """

    @property
    @abstractmethod
    def default_buffer_size(self) -> int:
        """Receive buffer size in bytes used for socket reads."""

        raise NotImplementedError

    @property
    @abstractmethod
    def default_timeout(self) -> float | None:
        """Default socket operation timeout in seconds, or ``None`` for no timeout."""

        raise NotImplementedError

    @abstractmethod
    def iter_library_paths(self) -> Generator["Path", None, None]:
        """Yield the resolved paths of all valid library scripts.

        Implementations should iterate over the configured library directory,
        filtering by allowed extensions, and yield each qualifying file path.

        Yields:
            ``Path`` objects pointing to individual library script files.
        """

        raise NotImplementedError

    @abstractmethod
    def resolve_module_path(self, module_filename: str, /) -> "Path":
        """Resolve and validate a module filename into a safe filesystem path.

        Ensures that the resulting path stays within the configured module root
        directory (path-traversal guard).

        Args:
            module_filename: Filename of the module relative to the module root.

        Returns:
            The fully resolved ``Path`` to the module file.

        Raises:
            InvalidOperation: If the resolved path escapes the module root.
        """

        raise NotImplementedError

    @abstractmethod
    def render_operation_command(self, opcode: "OperationCode", /, *args: str) -> str | None:
        """Build the shell command string for a given operation code.

        Maps an ``OperationCode`` to its client-side function name and appends
        each argument as a shell-quoted token. Returns ``None`` if the opcode
        is not supported by this profile.

        Args:
            opcode: The operation to invoke on the client.
            *args: Positional string arguments forwarded to the client function.

        Returns:
            A ready-to-send command string, or ``None`` if the opcode is unsupported.
        """

        raise NotImplementedError

    @abstractmethod
    def render_client_script(self, host: str, port: int, /) -> str:
        """Load the client script template and substitute connection parameters.

        Reads the script template from disk and replaces placeholders with the
        provided *host* and *port* values.

        Args:
            host: The server hostname or IP address to embed in the script.
            port: The port number to embed in the script.

        Returns:
            The fully rendered client script as a string.

        Raises:
            ConnectionFailure: If the template file cannot be read.
        """

        raise NotImplementedError


class IConnection(ABC):
    """Manages an active network session with a remote client.

    Handles the full lifecycle of a connection: initialization (handshake),
    framed read/write over the transport layer, and graceful shutdown.
    Supports the context manager protocol — ``close()`` is called automatically
    on exit.
    """

    @property
    @abstractmethod
    def client(self) -> "IConnectionProfile":
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
