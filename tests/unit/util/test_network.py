import socket
import threading
import time

import pytest

from declusor import config
from declusor.util import network


class TestHandleSocketException:
    """Verify socket error translation to domain ConnectionError."""

    def test_handle_socket_exception__gaierror__raises_connection_error_with_address_message(self) -> None:
        """Verify socket.gaierror is mapped to ConnectionError with invalid address message."""

        orig_err = socket.gaierror("getaddrinfo failed")

        with pytest.raises(config.ConnectionError, match="invalid address/hostname.") as exc_info:
            network._handle_socket_exception(orig_err)

        assert exc_info.value.__cause__ is orig_err

    def test_handle_socket_exception__overflow_error__raises_connection_error_with_port_message(self) -> None:
        """Verify OverflowError is mapped to ConnectionError with port range message."""

        orig_err = OverflowError("port out of range")

        with pytest.raises(config.ConnectionError, match=r"port must be 0-65535\.") as exc_info:
            network._handle_socket_exception(orig_err)

        assert exc_info.value.__cause__ is orig_err

    def test_handle_socket_exception__permission_error__raises_connection_error_with_permission_message(self) -> None:
        """Verify PermissionError is mapped to ConnectionError with permission denied message."""

        orig_err = PermissionError("bind denied")

        with pytest.raises(config.ConnectionError, match="permission denied.") as exc_info:
            network._handle_socket_exception(orig_err)

        assert exc_info.value.__cause__ is orig_err

    def test_handle_socket_exception__timeout_error__raises_connection_error_with_timeout_message(self) -> None:
        """Verify TimeoutError is mapped to ConnectionError with timeout message."""

        orig_err = TimeoutError("timed out")

        with pytest.raises(config.ConnectionError, match="connection timed out waiting for incoming connection.") as exc_info:
            network._handle_socket_exception(orig_err)

        assert exc_info.value.__cause__ is orig_err

    def test_handle_socket_exception__unmapped_exception__reraises_original_exception(self) -> None:
        """Verify unmapped generic exceptions are re-raised directly."""

        custom_err = RuntimeError("unhandled internal failure")

        with pytest.raises(RuntimeError, match="unhandled internal failure") as exc_info:
            network._handle_socket_exception(custom_err)

        assert exc_info.value is custom_err

    def test_handle_socket_exception__os_error_unmapped__reraises_original_exception(self) -> None:
        """Verify unmapped OSError types are re-raised without translation."""

        os_err = OSError(100, "custom os error")

        with pytest.raises(OSError) as exc_info:
            network._handle_socket_exception(os_err)

        assert exc_info.value is os_err


class TestAwaitConnection:
    """Verify await_connection listener lifecycle and client socket yielding."""

    def test_await_connection__client_connects__yields_connected_socket(self) -> None:
        """Verify await_connection accepts incoming client connection and yields connected socket."""

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]

        client_received: bytes = b""

        def client_worker() -> None:
            nonlocal client_received
            time.sleep(0.02)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_sock:
                client_sock.connect(("127.0.0.1", port))
                client_sock.sendall(b"client_hello")
                client_received = client_sock.recv(1024)

        client_thread = threading.Thread(target=client_worker, daemon=True)
        client_thread.start()

        try:
            with network.await_connection("127.0.0.1", port, timeout=2.0) as server_conn:
                msg = server_conn.recv(1024)
                assert msg == b"client_hello"
                server_conn.sendall(b"server_welcome")
        finally:
            client_thread.join(timeout=2.0)

        assert client_received == b"server_welcome"

    def test_await_connection__without_timeout__leaves_blocking_mode(self) -> None:
        """Verify await_connection with timeout=None accepts connection without setting timeout."""

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]

        def client_worker() -> None:
            time.sleep(0.02)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_sock:
                client_sock.connect(("127.0.0.1", port))

        client_thread = threading.Thread(target=client_worker, daemon=True)
        client_thread.start()

        try:
            with network.await_connection("127.0.0.1", port, timeout=None) as server_conn:
                assert server_conn is not None
        finally:
            client_thread.join(timeout=2.0)

    def test_await_connection__port_overflow__raises_connection_error(self) -> None:
        """Verify await_connection raises ConnectionError when port number exceeds 65535."""

        with pytest.raises(config.ConnectionError, match=r"port must be 0-65535\."):
            with network.await_connection("127.0.0.1", 999999):
                pass

    def test_await_connection__negative_port__raises_connection_error(self) -> None:
        """Verify await_connection raises ConnectionError when port number is negative."""

        with pytest.raises(config.ConnectionError, match=r"port must be 0-65535\."):
            with network.await_connection("127.0.0.1", -1):
                pass

    def test_await_connection__timeout_expires__raises_connection_error(self) -> None:
        """Verify await_connection raises ConnectionError when timeout expires with no incoming client."""

        with pytest.raises(config.ConnectionError, match="connection timed out waiting for incoming connection."):
            with network.await_connection("127.0.0.1", 0, timeout=0.01):
                pass

    def test_await_connection__invalid_hostname__raises_connection_error(self) -> None:
        """Verify await_connection raises ConnectionError when binding to an unresolvable hostname."""

        with pytest.raises(config.ConnectionError, match="invalid address/hostname."):
            with network.await_connection("invalid.domain.that.cannot.exist", 9000):
                pass

    def test_await_connection__unhandled_exception_in_body__reraises_without_mapping(self) -> None:
        """Verify exceptions occurring inside the context manager body are re-raised without translation."""

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]

        def client_worker() -> None:
            time.sleep(0.02)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_sock:
                client_sock.connect(("127.0.0.1", port))

        client_thread = threading.Thread(target=client_worker, daemon=True)
        client_thread.start()

        try:
            with pytest.raises(KeyError, match="body_error"):
                with network.await_connection("127.0.0.1", port, timeout=2.0):
                    raise KeyError("body_error")
        finally:
            client_thread.join(timeout=2.0)
