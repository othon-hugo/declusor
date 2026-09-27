import socket

import pytest

from declusor import config, transport


def test_tcp_listener_bind_ephemeral_port_and_accept() -> None:
    """Verify TcpListener binds to an ephemeral port and accepts incoming connections."""

    listener = transport.TcpListener("127.0.0.1", 0)
    try:
        assert not listener.is_closed
        assert listener.port > 0
        assert listener.local_endpoint == f"127.0.0.1:{listener.port}"

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect(("127.0.0.1", listener.port))
            accepted_transport = listener.accept(timeout=1.0)
            try:
                assert not accepted_transport.is_closed
                accepted_transport.write(b"welcome")
                assert client.recv(1024) == b"welcome"
            finally:
                accepted_transport.close()
        finally:
            client.close()
    finally:
        listener.close()
        assert listener.is_closed


def test_tcp_listener_accept_timeout() -> None:
    """Verify accept raises ConnectionTimeoutError when timeout expires."""

    listener = transport.TcpListener("127.0.0.1", 0)
    try:
        with pytest.raises(config.ConnectionTimeoutError, match="Timed out after 0.05s"):
            listener.accept(timeout=0.05)
    finally:
        listener.close()


def test_tcp_listener_accept_on_closed_listener_raises_connection_closed() -> None:
    """Verify accept raises ConnectionClosed when called on a closed listener."""

    listener = transport.TcpListener("127.0.0.1", 0)
    listener.close()

    with pytest.raises(config.ConnectionClosed, match="Cannot accept on closed listener"):
        listener.accept(timeout=0.1)


def test_tcp_listener_close_is_idempotent() -> None:
    """Verify close can be called multiple times without raising errors."""

    listener = transport.TcpListener("127.0.0.1", 0)
    listener.close()
    listener.close()
    assert listener.is_closed


def test_tcp_listener_context_manager() -> None:
    """Verify context manager automatically closes the listener on exit."""

    with transport.TcpListener("127.0.0.1", 0) as listener:
        assert not listener.is_closed
    assert listener.is_closed
