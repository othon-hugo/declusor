"""Unit tests for TcpListener.

Note: TcpListener is the concrete network adapter implementing contract.ITransportListener
by instantiating socket.socket(AF_INET, SOCK_STREAM). In accordance with the controlled resource
boundary in tests/README.md,
loopback sockets (127.0.0.1 on ephemeral port 0) are used with deterministic fixture teardown
because TcpListener directly bridges the OS socket kernel API to the Declusor transport layer.
"""

import socket
from collections.abc import Generator

import pytest

from declusor import config, transport


@pytest.fixture
def tcp_listener() -> Generator[transport.TcpListener, None, None]:
    """Provide an active loopback TcpListener with deterministic cleanup."""

    listener = transport.TcpListener("127.0.0.1", 0)
    try:
        yield listener
    finally:
        listener.close()


@pytest.fixture
def client_socket() -> Generator[socket.socket, None, None]:
    """Provide a client socket with deterministic cleanup."""

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        yield sock
    finally:
        sock.close()


class TestTcpListenerLifecycle:
    """Tests for TcpListener initialization, binding, and lifecycle management."""

    @pytest.mark.parametrize("port", [-1, 65536])
    def test_tcp_listener_init__out_of_range_port__raises_value_error(self, port: int) -> None:
        """Reject invalid port values before opening a socket."""

        with pytest.raises(ValueError, match="Port must be between 0 and 65535"):
            transport.TcpListener("127.0.0.1", port)

    @pytest.mark.parametrize("backlog", [0, -1])
    def test_tcp_listener_init__non_positive_backlog__raises_value_error(self, backlog: int) -> None:
        """Reject invalid connection backlog values before opening a socket."""

        with pytest.raises(ValueError, match="Backlog must be positive"):
            transport.TcpListener("127.0.0.1", 0, backlog)

    def test_tcp_listener_init__ephemeral_port__binds_and_retrieves_assigned_port(self, tcp_listener: transport.TcpListener) -> None:
        """Verify binding with port=0 assigns an active OS ephemeral port."""

        assert not tcp_listener.is_closed
        assert tcp_listener.port > 0

    def test_tcp_listener_init__privileged_port__raises_connection_error(self) -> None:
        """Verify attempting to bind a privileged port (<1024) raises ConnectionError."""

        with pytest.raises(config.ConnectionError, match="Failed to bind TCP listener on 127.0.0.1:1") as exc_info:
            transport.TcpListener("127.0.0.1", 1)

        assert isinstance(exc_info.value.__cause__, OSError)

    def test_tcp_listener_init__invalid_hostname__raises_connection_error(self) -> None:
        """Verify attempting to bind an unresolvable hostname raises ConnectionError."""

        with pytest.raises(config.ConnectionError, match="Failed to bind TCP listener") as exc_info:
            transport.TcpListener("999.999.999.999", 0)

        assert isinstance(exc_info.value.__cause__, OSError)

    def test_tcp_listener_properties__bound_listener__returns_host_port_and_endpoint(self, tcp_listener: transport.TcpListener) -> None:
        """Verify host, port, and local_endpoint properties return accurate descriptions."""

        assert tcp_listener.host == "127.0.0.1"
        assert tcp_listener.port > 0
        assert tcp_listener.local_endpoint == f"127.0.0.1:{tcp_listener.port}"

    def test_tcp_listener_is_closed__open_and_closed__reports_correct_state(self, tcp_listener: transport.TcpListener) -> None:
        """Verify is_closed accurately tracks listener lifecycle."""

        assert not tcp_listener.is_closed
        tcp_listener.close()
        assert tcp_listener.is_closed

    def test_tcp_listener_close__open_listener__closes_socket_and_marks_is_closed(self, tcp_listener: transport.TcpListener) -> None:
        """Verify close marks listener as closed and releases socket."""

        tcp_listener.close()

        assert tcp_listener.is_closed

    def test_tcp_listener_close__repeated_calls__is_idempotent(self, tcp_listener: transport.TcpListener) -> None:
        """Verify multiple calls to close do not raise an error."""

        tcp_listener.close()
        tcp_listener.close()

        assert tcp_listener.is_closed

    def test_tcp_listener_context_manager__exit__closes_listener(self) -> None:
        """Verify context manager automatically closes the listener on exit."""

        with transport.TcpListener("127.0.0.1", 0) as listener:
            assert not listener.is_closed

        assert listener.is_closed


class TestTcpListenerAccept:
    """Tests for incoming connection acceptance and timeout handling."""

    def test_tcp_listener_accept__already_closed_listener__raises_connection_closed(self, tcp_listener: transport.TcpListener) -> None:
        """Verify accept raises ConnectionClosed when invoked on a closed listener."""

        tcp_listener.close()

        with pytest.raises(config.ConnectionClosed, match="Cannot accept on closed listener"):
            tcp_listener.accept(timeout=0.1)

    def test_tcp_listener_accept__timeout_expired__raises_connection_timeout_error(self, tcp_listener: transport.TcpListener) -> None:
        """Verify accept raises ConnectionTimeoutError when timeout expires with no connection."""

        with pytest.raises(config.ConnectionTimeoutError, match="Timed out after 0.05s") as exc_info:
            tcp_listener.accept(timeout=0.05)

        assert isinstance(exc_info.value.__cause__, TimeoutError)

    def test_tcp_listener_accept__incoming_connection__returns_socket_transport(
        self,
        tcp_listener: transport.TcpListener,
        client_socket: socket.socket,
    ) -> None:
        """Verify accept receives incoming client and wraps into SocketTransport."""

        client_socket.connect(("127.0.0.1", tcp_listener.port))
        accepted = tcp_listener.accept(timeout=1.0)

        try:
            assert isinstance(accepted, transport.SocketTransport)
            assert not accepted.is_closed
        finally:
            accepted.close()

    def test_tcp_listener_accept__bidirectional_transmission__transfers_bytes_accurately(
        self,
        tcp_listener: transport.TcpListener,
        client_socket: socket.socket,
    ) -> None:
        """Verify bidirectional data transfer between client socket and accepted transport."""

        client_socket.connect(("127.0.0.1", tcp_listener.port))
        accepted = tcp_listener.accept(timeout=1.0)

        try:
            # Client sends to server
            client_socket.sendall(b"client hello")
            server_recv = accepted.read(1024)
            assert server_recv == b"client hello"

            # Server replies to client
            accepted.write(b"server welcome")
            client_recv = client_socket.recv(1024)
            assert client_recv == b"server welcome"
        finally:
            accepted.close()
