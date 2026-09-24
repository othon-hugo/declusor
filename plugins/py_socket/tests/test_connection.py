"""Unit tests for PySocketConnection."""

from socket import socket
from typing import cast

from declusor.testing import DummyClientFileStore, DummySocket
from plugins import py_socket


def test_py_socket_connection_write_sends_null_delimited_frame(
    dummy_file_store: DummyClientFileStore,
) -> None:
    """Verify PySocketConnection transmits data with null byte framing."""
    dummy_sock = DummySocket(incoming_bytes=b"\x00")
    profile = py_socket.PySocketProfile(name="test", ack_server_raw=b"\x00", ack_client_raw=b"\xab" * 32)

    conn = py_socket.PySocketConnection(cast(socket, dummy_sock), profile, dummy_file_store)
    conn.write(b"data")

    assert dummy_sock.sendall_calls == [b"data\x00"]
    assert dummy_sock.recv_calls == [len(b"\x00")]


def test_py_socket_connection_close_is_idempotent(
    dummy_file_store: DummyClientFileStore,
) -> None:
    """Verify closing PySocketConnection multiple times is idempotent."""
    dummy_sock = DummySocket()
    profile = py_socket.PySocketProfile(name="test", ack_server_raw=b"\x00", ack_client_raw=b"\xab" * 32)

    conn = py_socket.PySocketConnection(cast(socket, dummy_sock), profile, dummy_file_store)
    conn.close()
    conn.close()

    assert dummy_sock.close_calls == 1
    assert dummy_sock.closed is True
