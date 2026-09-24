import socket
from collections.abc import Generator
from contextlib import contextmanager

from declusor import config


@contextmanager
def await_connection(host: str, port: int, timeout: float | None = None) -> Generator[socket.socket, None, None]:
    """Context manager that listens for incoming connections on a specified host and port.

    Args:
        host: The hostname or IP address to bind to.
        port: The port number to bind to.
        timeout: Optional timeout in seconds to wait for an incoming connection.

    Yields:
        The connected socket object.

    Raises:
        ConnectionFailure: If a socket error occurs (e.g., invalid address, port out of range, permission denied, timeout).
    """

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            sock.listen(1)

            if timeout is not None:
                sock.settimeout(timeout)

            with sock.accept()[0] as connection:
                yield connection
        except Exception as e:
            _handle_socket_exception(e)


def _handle_socket_exception(e: Exception) -> None:
    """Handle socket-related exceptions and provide user-friendly error messages.

    Args:
        e: The exception that was raised.

    Raises:
        ConnectionFailure: With a user-friendly error message if the exception is known.
        Exception: Re-raises the original exception if it is not handled.
    """

    exception_message_table: dict[type[BaseException], str] = {
        socket.gaierror: "invalid address/hostname.",
        OverflowError: "port must be 0-65535.",
        PermissionError: "permission denied.",
        TimeoutError: "connection timed out waiting for incoming connection.",
    }

    for exception_type, exception_message in exception_message_table.items():
        if isinstance(e, exception_type):
            raise config.DeclusorException(exception_message) from e

    raise e from e
