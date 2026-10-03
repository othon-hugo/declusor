"""Unit tests for SocketTransport wrapping socket doubles."""

import socket
from typing import cast

import pytest

from declusor import config, testing, transport


def make_transport(sock: testing.DummySocket) -> transport.SocketTransport:
    """Helper to instantiate SocketTransport wrapping a typed DummySocket double."""

    return transport.SocketTransport(cast(socket.socket, sock))


class FailingPeerSocket(testing.DummySocket):
    """DummySocket whose getpeername raises OSError."""

    def getpeername(self) -> tuple[str, int]:
        """Raise OSError to simulate disconnected socket."""

        raise OSError("Transport endpoint is not connected")


class StringPeerSocket(testing.DummySocket):
    """DummySocket whose getpeername returns a string (e.g. Unix socket)."""

    def getpeername(self) -> str:  # type: ignore[override]
        """Return a string address representation."""

        return "/var/run/declusor.sock"


class ErrorCloseSocket(testing.DummySocket):
    """DummySocket whose close raises OSError."""

    def close(self) -> None:
        """Close socket and raise OSError to test error suppression."""

        super().close()
        raise OSError("Close failure")


class TestSocketTransportLifecycle:
    """Tests for SocketTransport initialization, properties, and lifecycle management."""

    def test_socket_transport_init__open_socket__initializes_as_open(self) -> None:
        """Verify SocketTransport initializes with is_closed=False."""

        sock = testing.DummySocket()
        trans = make_transport(sock)

        assert not trans.is_closed

    def test_socket_transport_raw_socket__getter__returns_underlying_socket(self) -> None:
        """Verify raw_socket returns the underlying socket instance."""

        sock = testing.DummySocket()
        trans = make_transport(sock)

        assert trans.rawsocket is cast(socket.socket, sock)

    def test_socket_transport_is_closed__open_and_closed__reports_correct_state(self) -> None:
        """Verify is_closed reflects the transport closure state."""

        sock = testing.DummySocket()
        trans = make_transport(sock)

        assert not trans.is_closed
        trans.close()
        assert trans.is_closed

    def test_socket_transport_timeout__getter_and_setter__delegates_to_socket(self) -> None:
        """Verify timeout getter and setter delegate directly to underlying socket."""

        sock = testing.DummySocket(timeout=1.0)
        trans = make_transport(sock)

        assert trans.timeout == 1.0

        trans.timeout = 5.0
        assert trans.timeout == 5.0
        assert sock.timeout == 5.0

    def test_socket_transport_peer_address__ip_port_tuple__formats_host_and_port(self) -> None:
        """Verify peer_address formats tuple endpoints as 'host:port'."""

        sock = testing.DummySocket(peer_name=("192.168.1.10", 8080))
        trans = make_transport(sock)

        assert trans.peer_address == "192.168.1.10:8080"

    def test_socket_transport_peer_address__string_peer__returns_string_representation(self) -> None:
        """Verify peer_address converts non-tuple endpoint representations to string."""

        sock = StringPeerSocket()
        trans = make_transport(sock)

        assert trans.peer_address == "/var/run/declusor.sock"

    def test_socket_transport_peer_address__os_error__returns_unknown(self) -> None:
        """Verify peer_address catches OSError from getpeername and returns 'unknown'."""

        sock = FailingPeerSocket()
        trans = make_transport(sock)

        assert trans.peer_address == "unknown"

    def test_socket_transport_close__open_transport__shuts_down_and_closes_socket(self) -> None:
        """Verify close invokes shutdown and close on the underlying socket."""

        sock = testing.DummySocket()
        trans = make_transport(sock)

        trans.close()

        assert trans.is_closed
        assert sock.shutdown_called
        assert sock.closed

    def test_socket_transport_close__repeated_calls__is_idempotent(self) -> None:
        """Verify repeated calls to close do not re-invoke socket shutdown or close."""

        sock = testing.DummySocket()
        trans = make_transport(sock)

        trans.close()
        trans.close()

        assert trans.is_closed
        assert sock.close_calls == 1

    def test_socket_transport_close__shutdown_or_close_os_error__suppresses_error(self) -> None:
        """Verify close suppresses OSErrors during socket shutdown and close."""

        sock = ErrorCloseSocket()
        sock.shutdown_error = OSError("shutdown error")
        trans = make_transport(sock)

        trans.close()

        assert trans.is_closed

    def test_socket_transport_context_manager__exit__closes_transport(self) -> None:
        """Verify context manager exit automatically closes the transport."""

        sock = testing.DummySocket()

        with make_transport(sock) as trans:
            assert not trans.is_closed

        assert trans.is_closed
        assert sock.closed


class TestSocketTransportRead:
    """Tests for SocketTransport read operations and exception mapping."""

    def test_socket_transport_read__closed_transport__raises_connection_closed(self) -> None:
        """Verify read on a closed transport raises ConnectionClosed."""

        sock = testing.DummySocket()
        trans = make_transport(sock)
        trans.close()

        with pytest.raises(config.ConnectionClosed, match="Cannot read from closed transport"):
            trans.read(1024)

    def test_socket_transport_read__incoming_data__returns_received_bytes(self) -> None:
        """Verify read returns bytes received from socket."""

        sock = testing.DummySocket(incoming_bytes=b"hello transport")
        trans = make_transport(sock)

        data = trans.read(1024)

        assert data == b"hello transport"

    def test_socket_transport_read__eof__returns_empty_bytes(self) -> None:
        """Verify read returns empty bytes b'' when socket receives EOF."""

        sock = testing.DummySocket(incoming_bytes=b"")
        trans = make_transport(sock)

        assert trans.read(1024) == b""

    def test_socket_transport_read__timeout_error__raises_connection_timeout_error(self) -> None:
        """Verify TimeoutError during read is wrapped into ConnectionTimeoutError."""

        sock = testing.DummySocket()
        sock.recv_error = TimeoutError("timed out")
        trans = make_transport(sock)

        with pytest.raises(config.ConnectionTimeoutError, match="Socket read timed out") as exc_info:
            trans.read(1024)

        assert isinstance(exc_info.value.__cause__, TimeoutError)

    def test_socket_transport_read__connection_reset_error__closes_transport_and_raises_connection_closed(
        self,
    ) -> None:
        """Verify ConnectionResetError closes transport and raises ConnectionClosed."""

        sock = testing.DummySocket()
        sock.recv_error = ConnectionResetError("reset by peer")
        trans = make_transport(sock)

        with pytest.raises(config.ConnectionClosed, match="Socket connection closed") as exc_info:
            trans.read(1024)

        assert trans.is_closed
        assert isinstance(exc_info.value.__cause__, ConnectionResetError)

    def test_socket_transport_read__connection_aborted_error__closes_transport_and_raises_connection_closed(
        self,
    ) -> None:
        """Verify ConnectionAbortedError closes transport and raises ConnectionClosed."""

        sock = testing.DummySocket()
        sock.recv_error = ConnectionAbortedError("aborted")
        trans = make_transport(sock)

        with pytest.raises(config.ConnectionClosed, match="Socket connection closed") as exc_info:
            trans.read(1024)

        assert trans.is_closed
        assert isinstance(exc_info.value.__cause__, ConnectionAbortedError)

    def test_socket_transport_read__broken_pipe_error__closes_transport_and_raises_connection_closed(
        self,
    ) -> None:
        """Verify BrokenPipeError closes transport and raises ConnectionClosed."""

        sock = testing.DummySocket()
        sock.recv_error = BrokenPipeError("broken pipe")
        trans = make_transport(sock)

        with pytest.raises(config.ConnectionClosed, match="Socket connection closed") as exc_info:
            trans.read(1024)

        assert trans.is_closed
        assert isinstance(exc_info.value.__cause__, BrokenPipeError)

    def test_socket_transport_read__os_error__raises_connection_error(self) -> None:
        """Verify general OSError during read is wrapped into ConnectionError."""

        sock = testing.DummySocket()
        sock.recv_error = OSError("generic I/O failure")
        trans = make_transport(sock)

        with pytest.raises(config.ConnectionError, match="Socket read error") as exc_info:
            trans.read(1024)

        assert isinstance(exc_info.value.__cause__, OSError)

    def test_socket_transport_read_exact__chunked_stream__accumulates_requested_bytes(self) -> None:
        """Verify read_exact accumulates discrete chunks until count is reached."""

        sock = testing.DummySocket()
        sock.feed_recv_chunks(b"123", b"4567", b"890")
        trans = make_transport(sock)

        result = trans.read_exact(10)

        assert result == b"1234567890"

    def test_socket_transport_read_exact__zero_count__returns_empty_bytes(self) -> None:
        """Verify read_exact(0) immediately returns b''."""

        sock = testing.DummySocket()
        trans = make_transport(sock)

        assert trans.read_exact(0) == b""

    def test_socket_transport_read_exact__negative_count__raises_value_error(self) -> None:
        """Verify read_exact rejects negative count with ValueError."""

        sock = testing.DummySocket()
        trans = make_transport(sock)

        with pytest.raises(ValueError, match="Count must be non-negative"):
            trans.read_exact(-1)

    def test_socket_transport_read_exact__premature_eof__raises_connection_closed(self) -> None:
        """Verify read_exact raises ConnectionClosed when EOF occurs before reading count bytes."""

        sock = testing.DummySocket(incoming_bytes=b"abc")
        trans = make_transport(sock)

        with pytest.raises(config.ConnectionClosed, match="Transport closed prematurely"):
            trans.read_exact(10)


class TestSocketTransportWrite:
    """Tests for SocketTransport write operations and exception mapping."""

    def test_socket_transport_write__closed_transport__raises_connection_closed(self) -> None:
        """Verify write on a closed transport raises ConnectionClosed."""

        sock = testing.DummySocket()
        trans = make_transport(sock)
        trans.close()

        with pytest.raises(config.ConnectionClosed, match="Cannot write to closed transport"):
            trans.write(b"data")

    def test_socket_transport_write__empty_bytes__is_noop_without_calling_sendall(self) -> None:
        """Verify write(b'') returns immediately without invoking sendall."""

        sock = testing.DummySocket()
        trans = make_transport(sock)

        trans.write(b"")

        assert sock.sendall_calls == []
        assert sock.sent_bytes == b""

    def test_socket_transport_write__valid_bytes__calls_sendall_with_data(self) -> None:
        """Verify write transmits full data byte buffer via sendall."""

        sock = testing.DummySocket()
        trans = make_transport(sock)

        trans.write(b"message payload")

        assert sock.sendall_calls == [b"message payload"]
        assert sock.sent_bytes == b"message payload"

    def test_socket_transport_write__timeout_error__raises_connection_timeout_error(self) -> None:
        """Verify TimeoutError during write is wrapped into ConnectionTimeoutError."""

        sock = testing.DummySocket()
        sock.sendall_error = TimeoutError("write timeout")
        trans = make_transport(sock)

        with pytest.raises(config.ConnectionTimeoutError, match="Socket write timed out") as exc_info:
            trans.write(b"payload")

        assert isinstance(exc_info.value.__cause__, TimeoutError)

    def test_socket_transport_write__connection_reset_error__closes_transport_and_raises_connection_closed(
        self,
    ) -> None:
        """Verify ConnectionResetError during write closes transport and raises ConnectionClosed."""

        sock = testing.DummySocket()
        sock.sendall_error = ConnectionResetError("write reset")
        trans = make_transport(sock)

        with pytest.raises(config.ConnectionClosed, match="Socket connection closed") as exc_info:
            trans.write(b"payload")

        assert trans.is_closed
        assert isinstance(exc_info.value.__cause__, ConnectionResetError)

    def test_socket_transport_write__connection_aborted_error__closes_transport_and_raises_connection_closed(
        self,
    ) -> None:
        """Verify ConnectionAbortedError during write closes transport and raises ConnectionClosed."""

        sock = testing.DummySocket()
        sock.sendall_error = ConnectionAbortedError("write aborted")
        trans = make_transport(sock)

        with pytest.raises(config.ConnectionClosed, match="Socket connection closed") as exc_info:
            trans.write(b"payload")

        assert trans.is_closed
        assert isinstance(exc_info.value.__cause__, ConnectionAbortedError)

    def test_socket_transport_write__broken_pipe_error__closes_transport_and_raises_connection_closed(
        self,
    ) -> None:
        """Verify BrokenPipeError during write closes transport and raises ConnectionClosed."""

        sock = testing.DummySocket()
        sock.sendall_error = BrokenPipeError("write broken pipe")
        trans = make_transport(sock)

        with pytest.raises(config.ConnectionClosed, match="Socket connection closed") as exc_info:
            trans.write(b"payload")

        assert trans.is_closed
        assert isinstance(exc_info.value.__cause__, BrokenPipeError)

    def test_socket_transport_write__os_error__raises_connection_error(self) -> None:
        """Verify general OSError during write is wrapped into ConnectionError."""

        sock = testing.DummySocket()
        sock.sendall_error = OSError("write hardware fault")
        trans = make_transport(sock)

        with pytest.raises(config.ConnectionError, match="Socket write error") as exc_info:
            trans.write(b"payload")

        assert isinstance(exc_info.value.__cause__, OSError)
