import socket

import pytest

from declusor import config, transport


def test_socket_transport_read_and_write_roundtrip() -> None:
    """Verify write transmits data and read receives it across a socket pair."""

    sock_a, sock_b = socket.socketpair()

    try:
        trans_a = transport.SocketTransport(sock_a)
        trans_b = transport.SocketTransport(sock_b)

        trans_a.write(b"hello from transport A")
        received = trans_b.read(4096)

        assert received == b"hello from transport A"
    finally:
        sock_a.close()
        sock_b.close()


def test_socket_transport_read_exact_accumulates_chunks() -> None:
    """Verify read_exact accumulates fragmented bytes until requested length."""

    sock_a, sock_b = socket.socketpair()

    try:
        trans_b = transport.SocketTransport(sock_b)

        sock_a.sendall(b"123")
        sock_a.sendall(b"4567")
        sock_a.sendall(b"890")

        result = trans_b.read_exact(10)
        assert result == b"1234567890"
    finally:
        sock_a.close()
        sock_b.close()


def test_socket_transport_read_returns_empty_bytes_on_eof() -> None:
    """Verify read returns b'' when the remote endpoint has closed."""

    sock_a, sock_b = socket.socketpair()
    trans_b = transport.SocketTransport(sock_b)

    sock_a.close()
    assert trans_b.read(1024) == b""
    trans_b.close()


def test_socket_transport_read_exact_raises_connection_closed_on_eof() -> None:
    """Verify read_exact raises ConnectionClosed on premature EOF."""

    sock_a, sock_b = socket.socketpair()
    trans_b = transport.SocketTransport(sock_b)

    sock_a.sendall(b"abc")
    sock_a.close()

    with pytest.raises(config.ConnectionClosed, match="Transport closed prematurely"):
        trans_b.read_exact(10)

    trans_b.close()


def test_socket_transport_timeout_management() -> None:
    """Verify timeout property gets and sets socket timeout."""

    sock_a, sock_b = socket.socketpair()

    try:
        trans = transport.SocketTransport(sock_a)
        assert trans.timeout is None

        trans.timeout = 0.5
        assert trans.timeout == 0.5
        assert sock_a.gettimeout() == 0.5
    finally:
        sock_a.close()
        sock_b.close()


def test_socket_transport_read_timeout_raises_connection_timeout_error() -> None:
    """Verify read raises ConnectionTimeoutError when socket timeout expires."""

    sock_a, sock_b = socket.socketpair()

    try:
        trans_b = transport.SocketTransport(sock_b)
        trans_b.timeout = 0.05

        with pytest.raises(config.ConnectionTimeoutError):
            trans_b.read(1024)
    finally:
        sock_a.close()
        sock_b.close()


def test_socket_transport_write_to_closed_transport_raises_connection_closed() -> None:
    """Verify write on a closed transport raises ConnectionClosed."""

    sock_a, sock_b = socket.socketpair()

    try:
        trans = transport.SocketTransport(sock_a)
        trans.close()
        assert trans.is_closed

        with pytest.raises(config.ConnectionClosed, match="Cannot write to closed transport"):
            trans.write(b"data")
    finally:
        sock_a.close()
        sock_b.close()


def test_socket_transport_read_from_closed_transport_raises_connection_closed() -> None:
    """Verify read on a closed transport raises ConnectionClosed."""

    sock_a, sock_b = socket.socketpair()

    try:
        trans = transport.SocketTransport(sock_a)
        trans.close()

        with pytest.raises(config.ConnectionClosed, match="Cannot read from closed transport"):
            trans.read(1024)
    finally:
        sock_a.close()
        sock_b.close()


def test_socket_transport_close_is_idempotent() -> None:
    """Verify closing SocketTransport multiple times is safe and idempotent."""

    sock_a, sock_b = socket.socketpair()

    try:
        trans = transport.SocketTransport(sock_a)
        trans.close()
        trans.close()
        assert trans.is_closed
    finally:
        sock_a.close()
        sock_b.close()


def test_socket_transport_context_manager() -> None:
    """Verify context manager automatically closes the socket on exit."""

    sock_a, sock_b = socket.socketpair()

    try:
        with transport.SocketTransport(sock_a) as trans:
            assert not trans.is_closed
        assert trans.is_closed
    finally:
        sock_b.close()
