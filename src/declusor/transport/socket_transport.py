import contextlib
import socket

from declusor import config, contract


class SocketTransport(contract.ITransport):
    """Production stream transport wrapping a connected Python socket.

    Translates low-level operating system socket exceptions (e.g. BrokenPipeError,
    ConnectionResetError, TimeoutError, OSError) into domain-level exceptions
    defined in declusor.config.
    """

    def __init__(self, sock: socket.socket, /) -> None:
        """Initialize the transport with an active socket."""

        self.socket = sock
        self._closed = False

    @property
    def is_closed(self) -> bool:
        """Return True if the transport channel is closed, False otherwise."""

        return self._closed

    @property
    def timeout(self) -> float | None:
        """Transport I/O timeout in seconds, or None for indefinite blocking."""

        return self.socket.gettimeout()

    @timeout.setter
    def timeout(self, value: float | None, /) -> None:
        """Set transport I/O timeout in seconds, or None for indefinite blocking."""

        self.socket.settimeout(value)

    @property
    def peer_address(self) -> str:
        """Representation of the remote endpoint (e.g. '192.168.1.10:4444')."""

        try:
            peer = self.socket.getpeername()
            if isinstance(peer, tuple) and len(peer) >= 2:
                return f"{peer[0]}:{peer[1]}"
            return str(peer)
        except OSError:
            return "unknown"

    @property
    def rawsocket(self) -> socket.socket:
        """Access the underlying OS socket."""

        return self.socket

    def read(self, max_bytes: int = 4096, /) -> bytes:
        """Read up to max_bytes from the socket.

        Args:
            max_bytes: Maximum number of bytes to read. Must be positive.

        Returns:
            The read bytes chunk. Returns empty bytes (b"") on EOF or remote closure.

        Raises:
            ValueError: If ``max_bytes`` is not positive.
            ConnectionTimeoutError: If read times out.
            ConnectionClosed: If called on a closed transport or remote closed reset.
            ConnectionError: On general socket I/O failure.
        """

        if max_bytes <= 0:
            raise ValueError(f"max_bytes must be positive, got {max_bytes}.")

        if self._closed:
            raise config.ConnectionClosed("Cannot read from closed transport.")

        try:
            data = self.socket.recv(max_bytes)
            if not data:
                return b""
            return data
        except TimeoutError as err:
            raise config.ConnectionTimeoutError(f"Socket read timed out: {err}") from err
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as err:
            self.close()
            raise config.ConnectionClosed(f"Socket connection closed: {err}") from err
        except OSError as err:
            raise config.ConnectionError(f"Socket read error: {err}") from err

    def write(self, data: bytes, /) -> None:
        """Transmit all bytes to the socket.

        Args:
            data: Raw bytes to send.

        Raises:
            ConnectionClosed: If called on a closed transport or connection reset.
            ConnectionTimeoutError: If transmission exceeds timeout.
            ConnectionError: On socket I/O failure.
        """

        if self._closed:
            raise config.ConnectionClosed("Cannot write to closed transport.")
        if not data:
            return

        try:
            self.socket.sendall(data)
        except TimeoutError as err:
            raise config.ConnectionTimeoutError(f"Socket write timed out: {err}") from err
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as err:
            self.close()
            raise config.ConnectionClosed(f"Socket connection closed: {err}") from err
        except OSError as err:
            raise config.ConnectionError(f"Socket write error: {err}") from err

    def close(self) -> None:
        """Close the socket and release OS resources idempotently."""

        if self._closed:
            return

        self._closed = True
        with contextlib.suppress(OSError):
            self.socket.shutdown(socket.SHUT_RDWR)

        with contextlib.suppress(OSError):
            self.socket.close()
