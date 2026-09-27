import declusor_py_socket as py_socket

from declusor import testing


def test_py_socket_connection_write_sends_null_delimited_frame(
    dummy_file_store: testing.DummyPluginFileStore,
) -> None:
    """Verify PySocketConnection transmits data with null byte framing."""

    dummy_trans = testing.DummyTransport()
    profile = py_socket.PySocketProfile(name="test", ack_server_raw=b"\x00", ack_client_raw=b"\xab" * 32)

    conn = py_socket.PySocketConnection(dummy_trans, profile, dummy_file_store)
    conn.write(b"data")

    assert dummy_trans.written_bytes == b"data\x00"
    assert dummy_trans.write_history == [b"data\x00"]


def test_py_socket_connection_close_is_idempotent(
    dummy_file_store: testing.DummyPluginFileStore,
) -> None:
    """Verify closing PySocketConnection multiple times is idempotent."""

    dummy_trans = testing.DummyTransport()
    profile = py_socket.PySocketProfile(name="test", ack_server_raw=b"\x00", ack_client_raw=b"\xab" * 32)

    conn = py_socket.PySocketConnection(dummy_trans, profile, dummy_file_store)
    conn.close()
    conn.close()

    assert dummy_trans.is_closed is True
