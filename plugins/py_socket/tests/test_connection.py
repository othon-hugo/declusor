import struct

import declusor_py_socket as py_socket
import pytest

from declusor import config, contract, testing


class TestPySocketConnectionLifecycle:
    """Tests for PySocketConnection lifecycle transitions and property accessors."""

    def test_handshake__when_successful__transitions_to_connected(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify PySocketConnection transmits helpers and transitions to CONNECTED on valid ACK."""

        dummy_trans = testing.DummyTransport()
        ack = b"\xab" * 32
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store, expected_ack=ack)

        dummy_trans.push_incoming(ack)
        conn.handshake()

        assert conn.state == contract.ConnectionState.CONNECTED
        expected_helpers_frame = struct.pack(">BI", config.ChannelType.STDOUT, len(dummy_file_store.helpers)) + dummy_file_store.helpers
        assert dummy_trans.write_history == [expected_helpers_frame]

    def test_handshake__when_connection_is_closed__raises_connection_error(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify handshake raises ConnectionError when connection is already closed."""

        dummy_trans = testing.DummyTransport()
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)
        conn.close()

        with pytest.raises(config.ConnectionError, match="Cannot initialize a closed connection"):
            conn.handshake()

    def test_handshake__when_ack_is_corrupted__raises_connection_handshake_error(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify handshake raises ConnectionHandshakeError when client ACK does not match expected hash."""

        dummy_trans = testing.DummyTransport()
        expected_ack = b"\xaa" * 32
        corrupted_ack = b"\xbb" * 32
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store, expected_ack=expected_ack)

        dummy_trans.push_incoming(corrupted_ack)

        with pytest.raises(config.ConnectionHandshakeError, match="Invalid client ACK during session initialization"):
            conn.handshake()

    def test_handshake__when_transport_fails__raises_connection_handshake_error(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify handshake raises ConnectionHandshakeError when transport write or read fails."""

        dummy_trans = testing.DummyTransport()
        dummy_trans.simulate_error_on_next_read(config.ConnectionError("read ACK failed"))
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)

        with pytest.raises(config.ConnectionHandshakeError, match="Failed waiting for client ACK"):
            conn.handshake()

    def test_close__repeated_calls__is_idempotent(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify closing PySocketConnection multiple times is idempotent and closes transport."""

        dummy_trans = testing.DummyTransport()
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)

        conn.close()
        conn.close()

        assert conn.state == contract.ConnectionState.CLOSED
        assert dummy_trans.is_closed is True

    def test_context_manager__closes_connection_on_exit(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify context manager automatically invokes close upon scope exit."""

        dummy_trans = testing.DummyTransport()
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)

        with conn as active_conn:
            assert active_conn is conn
            assert active_conn.state == contract.ConnectionState.CREATED

        assert conn.state == contract.ConnectionState.CLOSED
        assert dummy_trans.is_closed is True

    def test_properties__renderer_and_timeout__delegate_correctly(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify renderer, profile, and timeout property accessors and mutators."""

        dummy_trans = testing.DummyTransport()
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store, timeout=1.5)

        assert conn.renderer is renderer
        assert conn.profile is renderer
        assert conn.timeout == 1.5
        assert dummy_trans.timeout == 1.5

        conn.timeout = 3.0
        assert conn.timeout == 3.0
        assert dummy_trans.timeout == 3.0


class TestPySocketConnectionIO:
    """Tests for PySocketConnection read and write operations."""

    def test_write__sends_tlv_frame(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify write transmits data encapsulated in a 5-byte TLV frame."""

        dummy_trans = testing.DummyTransport()
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)

        conn.write(b"data")

        expected_frame = struct.pack(">BI", config.ChannelType.STDOUT, 4) + b"data"
        assert dummy_trans.written_bytes == expected_frame
        assert dummy_trans.write_history == [expected_frame]

    def test_write__when_connection_is_closed__raises_connection_closed(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify write on closed connection raises ConnectionClosed."""

        dummy_trans = testing.DummyTransport()
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)
        conn.close()

        with pytest.raises(config.ConnectionClosed, match="Connection is closed"):
            conn.write(b"data")

    def test_write__when_transport_fails__translates_to_connection_error(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify write translates transport write failure to domain ConnectionError."""

        dummy_trans = testing.DummyTransport()
        dummy_trans.simulate_error_on_next_write(config.ConnectionError("socket write failure"))
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)

        with pytest.raises(config.ConnectionError, match="Failed to write to connection"):
            conn.write(b"data")

    def test_read__streams_stdout_chunks_until_process_exit(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify read streams STDOUT chunks and terminates at PROCESS_EXIT frame."""

        dummy_trans = testing.DummyTransport()
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)

        frame1 = struct.pack(">BI", config.ChannelType.STDOUT, 6) + b"hello "
        frame2 = struct.pack(">BI", config.ChannelType.STDOUT, 5) + b"world"
        exit_frame = struct.pack(">BI", config.ChannelType.PROCESS_EXIT, 0)
        dummy_trans.push_incoming(frame1 + frame2 + exit_frame)

        chunks = list(conn.read())

        assert chunks == [b"hello ", b"world"]

    def test_read__streams_stderr_chunks(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify read yields STDERR chunks alongside STDOUT chunks."""

        dummy_trans = testing.DummyTransport()
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)

        err_frame = struct.pack(">BI", config.ChannelType.STDERR, 13) + b"error payload"
        exit_frame = struct.pack(">BI", config.ChannelType.PROCESS_EXIT, 0)
        dummy_trans.push_incoming(err_frame + exit_frame)

        chunks = list(conn.read())

        assert chunks == [b"error payload"]

    def test_read__when_exit_frame_has_payload__consumes_stream_cleanly(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify read consumes any payload attached to PROCESS_EXIT frame before terminating."""

        dummy_trans = testing.DummyTransport()
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)

        out_frame = struct.pack(">BI", config.ChannelType.STDOUT, 4) + b"done"
        exit_payload = b"exit code 0\n"
        exit_frame = struct.pack(">BI", config.ChannelType.PROCESS_EXIT, len(exit_payload)) + exit_payload
        dummy_trans.push_incoming(out_frame + exit_frame)

        chunks = list(conn.read())

        assert chunks == [b"done"]
        # All incoming bytes must have been consumed
        assert dummy_trans.read() == b""

    def test_read__when_connection_is_closed__raises_connection_closed(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify read on closed connection raises ConnectionClosed."""

        dummy_trans = testing.DummyTransport()
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)
        conn.close()

        with pytest.raises(config.ConnectionClosed, match="Connection is closed"):
            list(conn.read())

    def test_read__when_transport_interrupted__raises_connection_closed(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify read translates transport connection error into ConnectionClosed."""

        dummy_trans = testing.DummyTransport()
        dummy_trans.simulate_error_on_next_read(config.ConnectionError("peer disconnected"))
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)

        with pytest.raises(config.ConnectionClosed, match="Connection interrupted during read"):
            list(conn.read())

    def test_read__when_transport_times_out__propagates_timeout_error(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify read propagates ConnectionTimeoutError directly."""

        dummy_trans = testing.DummyTransport()
        dummy_trans.simulate_error_on_next_read(config.ConnectionTimeoutError("read timeout"))
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)

        with pytest.raises(config.ConnectionTimeoutError, match="read timeout"):
            list(conn.read())
