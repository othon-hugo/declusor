"""Tests for the ``declusor.util.network`` module."""

import socket

import pytest

from declusor import config
from declusor import mock
from declusor.util import network


# =============================================================================
# Tests: network.await_connection (Handling incoming connections)
# =============================================================================

def test_await_connection_yields_accepted_socket(mock_socket: mock.MockSocket) -> None:
    """Awaiting a connection must bind to the host and port and yield an accepted socket."""
    # ARRANGE: Save the original socket class and inject the mock implementation
    original_socket = network.socket.socket
    network.socket.socket = lambda *args, **kwargs: mock_socket  # type: ignore

    mock_connection = mock.MockSocket()
    mock_socket.accept_return = (mock_connection, ("127.0.0.1", 54321))

    try:
        # ACT: Use the context manager to await an incoming connection
        with network.await_connection("127.0.0.1", 8080) as conn:
            # ASSERT: The yielded socket should be the one returned by the mock accept
            assert conn is mock_connection

        # ASSERT: Ensure the server socket was correctly bound and listened
        assert mock_socket.bind_args == ("127.0.0.1", 8080)
        assert mock_socket.listen_arg == 1
    finally:
        network.socket.socket = original_socket


def test_await_connection_raises_connection_failure_on_invalid_address(mock_socket: mock.MockSocket) -> None:
    """Awaiting a connection on an invalid address must raise a ``ConnectionFailure``."""
    # ARRANGE: Inject the mock and configure it to simulate an invalid address error
    original_socket = network.socket.socket
    network.socket.socket = lambda *args, **kwargs: mock_socket  # type: ignore

    mock_socket.bind_exception = socket.gaierror("address invalid")

    try:
        # ACT & ASSERT: Attempting to connect should throw the standardized network wrapper error
        with pytest.raises(config.ConnectionFailure, match="invalid address/hostname"):
            with network.await_connection("invalid_host", 8080):
                pass
    finally:
        network.socket.socket = original_socket


def test_await_connection_raises_connection_failure_on_port_overflow(mock_socket: mock.MockSocket) -> None:
    """Awaiting a connection on an out-of-range port must raise a ``ConnectionFailure``."""
    # ARRANGE: Inject the mock and set it to raise an OverflowError (port > 65535)
    original_socket = network.socket.socket
    network.socket.socket = lambda *args, **kwargs: mock_socket  # type: ignore

    mock_socket.bind_exception = OverflowError("port must be 0-65535")

    try:
        # ACT & ASSERT: Verify the internal standard error representation is raised
        with pytest.raises(config.ConnectionFailure, match="port must be 0-65535"):
            with network.await_connection("127.0.0.1", 99999):
                pass
    finally:
        network.socket.socket = original_socket


def test_await_connection_raises_connection_failure_on_permission_denied(mock_socket: mock.MockSocket) -> None:
    """Awaiting a connection on a protected port without privileges must raise a ``ConnectionFailure``."""
    # ARRANGE: Inject the mock configured to simulate restricted port access denial
    original_socket = network.socket.socket
    network.socket.socket = lambda *args, **kwargs: mock_socket  # type: ignore

    mock_socket.bind_exception = PermissionError("permission denied")

    try:
        # ACT & ASSERT: Expect connection to fail with a tailored privilege access error
        with pytest.raises(config.ConnectionFailure, match="permission denied"):
            with network.await_connection("127.0.0.1", 22):
                pass
    finally:
        network.socket.socket = original_socket

def test_await_connection_raises_original_exception_if_unhandled(mock_socket: mock.MockSocket) -> None:
    """Awaiting a connection that breaks due to an unhandled internal exception must re-raise the original problem."""

    # ARRANGE: Inject the mock configured to raise an unrecognized internal exception
    original_socket = network.socket.socket
    network.socket.socket = lambda *args, **kwargs: mock_socket  # type: ignore

    mock_socket.bind_exception = RuntimeError("some generic unknown error")

    try:
        # ACT & ASSERT: Generic exceptions should skip transformation and float straight back to caller
        with pytest.raises(RuntimeError, match="some generic unknown error"):
            with network.await_connection("127.0.0.1", 8080):
                pass
    finally:
        network.socket.socket = original_socket
