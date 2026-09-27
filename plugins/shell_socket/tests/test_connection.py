from collections.abc import Callable

import declusor_shell_socket as shell_socket
import pytest

from declusor import config, contract, testing


def test_connection_state_lifecycle_transitions(
    make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
) -> None:
    """Verify connection lifecycle transitions: CREATED -> CONNECTED -> CLOSED."""

    trans = testing.DummyTransport(incoming_data=b"valid_ack_32_bytes_long_sentinel")

    conn, _ = make_shell_connection(trans, ack=b"valid_ack_32_bytes_long_sentinel")
    state: contract.ConnectionState = conn.state
    assert state == contract.ConnectionState.CREATED

    conn.handshake()
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
    make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
) -> None:
    """Verify ACK validation handles segmented byte streaming properly."""

    trans = testing.DummyTransport(
        incoming_data=[
            b"valid_ack_",
            b"32_bytes_",
            b"long_sentinel",
        ]
    )

    conn, _ = make_shell_connection(trans, ack=b"valid_ack_32_bytes_long_sentinel")
    conn.handshake()
    assert conn.state == contract.ConnectionState.CONNECTED


def test_initialize_fails_on_closed_connection(
    make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
) -> None:
    """Verify initialize raises ConnectionError when connection is already closed."""

    conn, _ = make_shell_connection()
    conn.close()

    with pytest.raises(config.ConnectionError, match="Cannot initialize a closed connection"):
        conn.handshake()


def test_write_uses_sendall_for_payload_and_ack(
    make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
) -> None:
    """Verify write transmits payload followed by null byte framing."""

    connection, trans = make_shell_connection()

    connection.write(b"command")
    assert trans.write_history == [b"command", b"\x00"]
    assert trans.written_bytes == b"command\x00"


def test_write_translates_transport_errors(
    make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
) -> None:
    """Verify write translates transport errors into domain ConnectionError."""

    trans = testing.DummyTransport()
    trans.simulate_error_on_next_write(config.ConnectionError("transport write failed"))

    connection, _ = make_shell_connection(trans)

    with pytest.raises(config.ConnectionError, match="Failed to write to connection"):
        connection.write(b"command")
