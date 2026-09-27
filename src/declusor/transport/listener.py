import contextlib
import socket as _socket

from declusor import config, contract

from .socket import SocketTransport


class TcpListener(contract.ITransportListener):
    """TCP server listener that binds an address and accepts SocketTransport clients."""

    def __init__(self, host: str, port: int, backlog: int = 5, /) -> None:
        """Bind and listen on the given host and port.

        Args:
            host: Interface IP or hostname to bind.
            port: Port number to bind (0 for OS-assigned ephemeral port).
            backlog: Connection backlog queue size.

        Raises:
            ConnectionError: If binding or listening fails.
        """

        self._host = host
        self._closed = False

        try:
            self._socket = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
            self._socket.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
            self._socket.bind((host, port))
            self._socket.listen(backlog)
            self._bound_port = int(self._socket.getsockname()[1])
        except OSError as err:
            self._closed = True
            raise config.ConnectionError(f"Failed to bind TCP listener on {host}:{port}: {err}") from err

    @property
    def is_closed(self) -> bool:
        """Return True if the listener is closed."""

        return self._closed

    @property
    def host(self) -> str:
        """Return the bound host."""

        return self._host

    @property
    def port(self) -> int:
        """Return the bound port number."""

        return self._bound_port

    @property
    def local_endpoint(self) -> str:
        """Return the local listening endpoint description (e.g. '0.0.0.0:9000')."""

        return f"{self._host}:{self._bound_port}"

    def accept(self, timeout: float | None = None) -> SocketTransport:
        """Wait for and return an accepted incoming SocketTransport.

        Args:
            timeout: Optional seconds to wait before timing out.

        Returns:
            An active SocketTransport wrapping the accepted client socket.

        Raises:
            ConnectionTimeoutError: If timeout expires without an incoming connection.
            ConnectionClosed: If called on a closed listener.
            ConnectionError: If accept fails due to OS network error.
        """

        if self._closed:
            raise config.ConnectionClosed("Cannot accept on closed listener.")

        self._socket.settimeout(timeout)

        try:
            client_sock, _ = self._socket.accept()
            return SocketTransport(client_sock)
        except TimeoutError as err:
            raise config.ConnectionTimeoutError(f"Timed out after {timeout}s waiting for incoming connection.") from err
        except OSError as err:
            if self._closed:
                raise config.ConnectionClosed("Listener was closed.") from err
            raise config.ConnectionError(f"Failed to accept connection: {err}") from err

    def close(self) -> None:
        """Stop listening and release the bound port idempotently."""

        if self._closed:
            return

        self._closed = True

        with contextlib.suppress(OSError):
            self._socket.close()
