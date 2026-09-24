import socket

import pytest

from declusor import config
from declusor.util import network


def test_handle_socket_exception_mapped_types() -> None:
    """Verify known socket exceptions are mapped to DeclusorException."""

    test_cases = [
        (socket.gaierror("getaddrinfo failed"), "invalid address/hostname."),
        (OverflowError("port out of range"), "port must be 0-65535."),
        (PermissionError("bind denied"), "permission denied."),
        (TimeoutError("timed out"), "connection timed out waiting for incoming connection."),
    ]

    for exc, expected_msg in test_cases:
        with pytest.raises(config.DeclusorException, match=expected_msg):
            network._handle_socket_exception(exc)


def test_handle_socket_exception_unmapped_type() -> None:
    """Verify unmapped exceptions are re-raised as-is."""

    custom_exc = RuntimeError("unhandled error")
    with pytest.raises(RuntimeError, match="unhandled error"):
        network._handle_socket_exception(custom_exc)


def test_await_connection_bind_error() -> None:
    """Verify await_connection raises DeclusorException on invalid port."""

    with pytest.raises(config.DeclusorException, match="port must be 0-65535."):
        with network.await_connection("127.0.0.1", 999999):
            pass


def test_await_connection_timeout() -> None:
    """Verify await_connection raises DeclusorException on timeout."""

    with pytest.raises(config.DeclusorException, match="connection timed out"):
        with network.await_connection("127.0.0.1", 0, timeout=0.01):
            pass
