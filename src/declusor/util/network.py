"""Low-level network socket creation and blocking listener context managers."""

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
        config.ConnectionError: If a recognized socket setup or accept failure occurs.
        Exception: If an unrecognized error occurs; the original exception is re-raised.
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
        config.ConnectionError: With a user-friendly message if the exception is recognized.
        Exception: Re-raises the original exception if it is not handled.
    """

    try:
        raise e
    except socket.gaierror as exc:
        raise config.ConnectionError("invalid address/hostname.") from exc
    except OverflowError as exc:
        raise config.ConnectionError("port must be 0-65535.") from exc
    except PermissionError as exc:
        raise config.ConnectionError("permission denied.") from exc
    except TimeoutError as exc:
        raise config.ConnectionError("connection timed out waiting for incoming connection.") from exc
    except Exception:
        raise
