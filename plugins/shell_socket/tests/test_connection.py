from collections.abc import Callable

import pytest
import shell_socket

from declusor import config, contract
from declusor.testing import DummySocket


def test_connection_state_lifecycle_transitions(
    make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, DummySocket]],
) -> None:
    """Verify connection lifecycle transitions: CREATED -> CONNECTED -> CLOSED."""
    sock = DummySocket(incoming_bytes=b"\x00" + b"valid_ack_32_bytes_long_sentinel")

    conn, _ = make_shell_connection(sock, ack=b"valid_ack_32_bytes_long_sentinel")
    state: contract.ConnectionState = conn.state
    assert state == contract.ConnectionState.CREATED

    conn.initialize()
    state = conn.state
    assert state == contract.ConnectionState.CONNECTED

    conn.close()
    state = conn.state
    assert state == contract.ConnectionState.CLOSED

    # Calling close again must be idempotent
    conn.close()
    state = conn.state
    assert state == contract.ConnectionState.CLOSED


def test_connection_segmented_ack_streaming(
    make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, DummySocket]],
) -> None:
    """Verify ACK validation handles segmented byte streaming properly."""
    sock = DummySocket()
    sock.feed_recv_chunks(
        b"\x00",
        b"valid_ack_",
        b"32_bytes_",
        b"long_sentinel",
    )

    conn, _ = make_shell_connection(sock, ack=b"valid_ack_32_bytes_long_sentinel")
    conn.initialize()
    assert conn.state == contract.ConnectionState.CONNECTED


def test_initialize_fails_on_closed_connection(
    make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, DummySocket]],
) -> None:
    """Verify initialize raises ConnectionError when connection is already closed."""
    conn, _ = make_shell_connection()
    conn.close()

    with pytest.raises(config.ConnectionError, match="Cannot initialize a closed connection"):
        conn.initialize()


def test_write_uses_sendall_for_payload_and_ack(
    make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, DummySocket]],
) -> None:
    """Verify write uses sendall to transmit payload followed by null byte framing."""
    connection, sock = make_shell_connection()

    connection.write(b"command")
    assert sock.sendall_calls == [b"command", b"\x00"]


@pytest.mark.parametrize("error", [OSError("broken pipe"), TimeoutError("timed out")])
def test_write_translates_transport_errors(
    make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, DummySocket]],
    error: BaseException,
) -> None:
    """Verify write translates socket transport errors into domain ConnectionError."""
    sock = DummySocket()
    sock.sendall_error = error

    connection, _ = make_shell_connection(sock)

    with pytest.raises(config.ConnectionError) as raised:
        connection.write(b"command")

    assert raised.value.__cause__ is error
