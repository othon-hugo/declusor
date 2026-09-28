import struct

import declusor_py_socket as py_socket

from declusor import config, contract, testing


def test_py_socket_connection_write_sends_tlv_frame(
    dummy_file_store: testing.DummyPluginFileStore,
) -> None:
    """Verify PySocketConnection transmits data with 5-byte TLV framing."""

    dummy_trans = testing.DummyTransport()
    profile = py_socket.PySocketProfile(name="test", ack_server_raw=b"\x00", ack_client_raw=b"\xab" * 32)

    conn = py_socket.PySocketConnection(dummy_trans, profile, dummy_file_store)
    conn.write(b"data")

    expected_frame = struct.pack(">BI", config.ChannelType.STDOUT, 4) + b"data"
    assert dummy_trans.written_bytes == expected_frame
    assert dummy_trans.write_history == [expected_frame]
    assert conn.last_exit_code is None


def test_py_socket_connection_read_tlv_frames_and_exit_code(
    dummy_file_store: testing.DummyPluginFileStore,
) -> None:
    """Verify PySocketConnection streams chunks and extracts exit code."""

    dummy_trans = testing.DummyTransport()
    profile = py_socket.PySocketProfile(name="test", ack_server_raw=b"\x00", ack_client_raw=b"\xab" * 32)
    conn = py_socket.PySocketConnection(dummy_trans, profile, dummy_file_store)

    frame1 = struct.pack(">BI", config.ChannelType.STDOUT, 6) + b"hello "
    frame2 = struct.pack(">BI", config.ChannelType.STDOUT, 5) + b"world"
    exit_frame = struct.pack(">BI", config.ChannelType.PROCESS_EXIT, 4) + struct.pack(">i", 42)

    dummy_trans.push_incoming(frame1 + frame2 + exit_frame)

    chunks = list(conn.read())
    assert chunks == [b"hello ", b"world"]
    assert conn.last_exit_code == 42


def test_py_socket_connection_handshake(
    dummy_file_store: testing.DummyPluginFileStore,
) -> None:
    """Verify PySocketConnection sends helpers as TLV frame and validates ACK."""

    dummy_trans = testing.DummyTransport()
    ack = b"\xab" * 32
    profile = py_socket.PySocketProfile(name="test", ack_server_raw=b"\x00", ack_client_raw=ack)
    conn = py_socket.PySocketConnection(dummy_trans, profile, dummy_file_store)

    dummy_trans.push_incoming(ack)
    conn.handshake()

    assert conn.state == contract.ConnectionState.CONNECTED
    expected_helpers_frame = struct.pack(">BI", config.ChannelType.STDOUT, len(dummy_file_store.helpers)) + dummy_file_store.helpers
    assert dummy_trans.write_history == [expected_helpers_frame]


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
