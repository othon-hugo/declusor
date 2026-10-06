import importlib.util
import json
import struct
import sys

import pytest
from declusor import config, contract, lang, testing

import declusor_py_socket as py_socket


def _make_metadata_frame(magic: bytes | None = None, version: list[int] | None = None) -> bytes:
    meta_dict = {
        "version": version or list(sys.version_info[:3]),
        "magic": (magic or importlib.util.MAGIC_NUMBER).hex(),
        "platform": sys.platform,
        "implementation": "CPython",
    }

    encoded = json.dumps(meta_dict).encode("utf-8")

    return struct.pack(">BI", config.ChannelType.STDOUT, len(encoded)) + encoded


class TestPySocketConnectionLifecycle:
    """Tests for PySocketConnection lifecycle transitions and property accessors."""

    def test_handshake__oversized_metadata_frame__rejects_before_reading_body(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Reject oversized metadata using its header before consuming the body."""

        monkeypatch.setattr(config, "MAX_TLV_FRAME_SIZE", 4)
        dummy_trans = testing.DummyTransport()
        dummy_trans.push_incoming(struct.pack(">BI", config.ChannelType.STDOUT, 5) + b"12345")
        conn = py_socket.PySocketConnection(dummy_trans, py_socket.PySocketRenderer(), dummy_file_store)

        with pytest.raises(config.ConnectionHandshakeError, match="Failed reading client runtime metadata"):
            conn.handshake()

        assert dummy_trans.write_history == []
        assert dummy_trans._incoming == [b"12345"]

    def test_handshake__when_successful_and_bytecode_compatible__transitions_to_connected(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify PySocketConnection transmits marshaled helpers when client bytecode is compatible."""

        dummy_trans = testing.DummyTransport()
        ack = b"\xab" * 32
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store, expected_ack=ack)

        meta = _make_metadata_frame()
        dummy_trans.push_incoming(meta + ack)
        conn.handshake()

        assert conn.state == contract.ConnectionState.CONNECTED
        assert conn.is_bytecode_compatible is True
        assert conn.client_runtime is not None

        expected_helpers = lang.python.compile_and_serialize(dummy_file_store.helpers.decode(), "<helpers>")
        expected_helpers_frame = struct.pack(">BI", config.ChannelType.STDIN, len(expected_helpers)) + expected_helpers
        assert dummy_trans.write_history == [expected_helpers_frame]

    def test_handshake__when_bytecode_incompatible__transmits_source_helpers(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify PySocketConnection transmits UTF-8 source helpers when bytecode is incompatible."""

        dummy_trans = testing.DummyTransport()
        ack = b"\xab" * 32
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store, expected_ack=ack)

        mismatched_magic = b"\x00\x00\x00\x00"
        meta = _make_metadata_frame(magic=mismatched_magic)
        dummy_trans.push_incoming(meta + ack)
        conn.handshake()

        assert conn.state == contract.ConnectionState.CONNECTED
        assert conn.is_bytecode_compatible is False

        expected_helpers_frame = struct.pack(">BI", config.ChannelType.STDIN, len(dummy_file_store.helpers)) + dummy_file_store.helpers
        assert dummy_trans.write_history == [expected_helpers_frame]

    def test_handshake__when_already_connected__raises_connection_error(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify handshake raises ConnectionError when connection is already connected."""

        dummy_trans = testing.DummyTransport()
        ack = b"\xab" * 32
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store, expected_ack=ack)

        meta = _make_metadata_frame()
        dummy_trans.push_incoming(meta + ack)
        conn.handshake()

        with pytest.raises(config.ConnectionError, match="Connection is already initialized"):
            conn.handshake()

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

        meta = _make_metadata_frame()
        dummy_trans.push_incoming(meta + corrupted_ack)

        with pytest.raises(config.ConnectionHandshakeError, match="Invalid client ACK during session initialization"):
            conn.handshake()

    def test_handshake__when_metadata_transport_fails__raises_connection_handshake_error(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify handshake raises ConnectionHandshakeError when reading metadata frame fails."""

        dummy_trans = testing.DummyTransport()
        dummy_trans.simulate_error_on_next_read(config.ConnectionError("read metadata failed"))
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)

        with pytest.raises(config.ConnectionHandshakeError, match="Failed reading client runtime metadata"):
            conn.handshake()

    def test_handshake__when_ack_transport_fails__raises_connection_handshake_error(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify handshake raises ConnectionHandshakeError when reading ACK fails."""

        class FailingAckTransport(testing.DummyTransport):
            def write(self, data: bytes, /) -> None:
                super().write(data)
                self.simulate_error_on_next_read(config.ConnectionError("read ACK failed"))

        trans = FailingAckTransport()
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(trans, renderer, dummy_file_store)

        meta = _make_metadata_frame()
        trans.push_incoming(meta)

        with pytest.raises(config.ConnectionHandshakeError, match="Failed waiting for client ACK"):
            conn.handshake()

    def test_send_python_payload__when_bytecode_compatible__transmits_marshaled_bytecode(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify send_python_payload transmits marshaled bytecode when connection is bytecode compatible."""

        dummy_trans = testing.DummyTransport()
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)
        conn._state = contract.ConnectionState.CONNECTED
        conn._is_bytecode_compatible = True

        conn.send_python_payload("answer = 42\n")

        # Extract payload from TLV frame
        written = dummy_trans.written_bytes
        channel, length = struct.unpack(">BI", written[:5])
        payload = written[5 : 5 + length]

        assert channel == config.ChannelType.STDIN
        expected_payload = lang.python.compile_and_serialize("answer = 42\n", "<remote>")
        assert payload == expected_payload

    def test_send_python_payload__when_incompatible__transmits_utf8_source(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify send_python_payload transmits UTF-8 source string when bytecode incompatible."""

        dummy_trans = testing.DummyTransport()
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)
        conn._state = contract.ConnectionState.CONNECTED
        conn._is_bytecode_compatible = False

        conn.send_python_payload("answer = 42\n")

        written = dummy_trans.written_bytes
        channel, length = struct.unpack(">BI", written[:5])
        payload = written[5 : 5 + length]

        assert channel == config.ChannelType.STDIN
        assert payload == b"answer = 42\n"

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
        assert conn.timeout == 1.5
        assert dummy_trans.timeout == 1.5

        conn.timeout = 3.0
        assert conn.timeout == 3.0
        assert dummy_trans.timeout == 3.0


class TestPySocketConnectionIO:
    """Tests for PySocketConnection read and write operations."""

    def test_write__oversized_frame__raises_before_transport_write(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Reject oversized outgoing payloads before constructing a transport frame."""

        monkeypatch.setattr(config, "MAX_TLV_FRAME_SIZE", 4)
        dummy_trans = testing.DummyTransport()
        conn = py_socket.PySocketConnection(dummy_trans, py_socket.PySocketRenderer(), dummy_file_store)
        conn._state = contract.ConnectionState.CONNECTED

        with pytest.raises(ValueError, match="TLV frame payload exceeds maximum size"):
            conn.write(b"12345")

        assert dummy_trans.write_history == []

    def test_read__oversized_frame__closes_before_reading_body(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Reject oversized response payloads before reading their bodies and close the connection."""

        monkeypatch.setattr(config, "MAX_TLV_FRAME_SIZE", 4)
        dummy_trans = testing.DummyTransport()
        dummy_trans.push_incoming(struct.pack(">BI", config.ChannelType.STDOUT, 5) + b"12345")
        conn = py_socket.PySocketConnection(dummy_trans, py_socket.PySocketRenderer(), dummy_file_store)
        conn._state = contract.ConnectionState.CONNECTED

        with pytest.raises(config.ConnectionClosed, match="TLV frame payload size 5 exceeds maximum 4"):
            list(conn.read())

        assert conn.is_closed
        assert dummy_trans.is_closed
        assert dummy_trans._incoming == [b"12345"]

    def test_write__sends_tlv_frame(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify write transmits data encapsulated in a 5-byte TLV frame on the STDIN bus."""

        dummy_trans = testing.DummyTransport()
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)
        conn._state = contract.ConnectionState.CONNECTED

        conn.write(b"data")

        expected_frame = struct.pack(">BI", config.ChannelType.STDIN, 4) + b"data"
        assert dummy_trans.written_bytes == expected_frame
        assert dummy_trans.write_history == [expected_frame]

    def test_write_frame__with_custom_channel__sends_custom_channel_in_tlv_frame(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify write_frame transmits custom channel identifier in 5-byte TLV frame."""

        dummy_trans = testing.DummyTransport()
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)
        conn._state = contract.ConnectionState.CONNECTED

        conn.write_frame(config.ChannelType.SIGNAL, b"data")

        expected_frame = struct.pack(">BI", config.ChannelType.SIGNAL, 4) + b"data"
        assert dummy_trans.written_bytes == expected_frame
        assert dummy_trans.write_history == [expected_frame]

    def test_write__when_connection_is_created__raises_connection_error(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify write on CREATED connection raises ConnectionError before handshake."""

        dummy_trans = testing.DummyTransport()
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)

        with pytest.raises(config.ConnectionError, match="Cannot perform I/O on connection that is not connected"):
            conn.write(b"data")

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
        conn._state = contract.ConnectionState.CONNECTED

        with pytest.raises(config.ConnectionError, match="Failed to write to connection"):
            conn.write(b"data")

    def test_read__when_connection_is_created__raises_connection_error(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify read on CREATED connection raises ConnectionError before handshake."""

        dummy_trans = testing.DummyTransport()
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)

        with pytest.raises(config.ConnectionError, match="Cannot perform I/O on connection that is not connected"):
            list(conn.read())

    def test_read__streams_stdout_chunks_until_process_exit(
        self,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """Verify read streams STDOUT chunks and terminates at PROCESS_EXIT frame."""

        dummy_trans = testing.DummyTransport()
        renderer = py_socket.PySocketRenderer()
        conn = py_socket.PySocketConnection(dummy_trans, renderer, dummy_file_store)
        conn._state = contract.ConnectionState.CONNECTED

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
        conn._state = contract.ConnectionState.CONNECTED

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
        conn._state = contract.ConnectionState.CONNECTED

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
        conn._state = contract.ConnectionState.CONNECTED

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
        conn._state = contract.ConnectionState.CONNECTED

        with pytest.raises(config.ConnectionTimeoutError, match="read timeout"):
            list(conn.read())
