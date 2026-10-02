from collections.abc import Callable
from pathlib import Path

import declusor_shell_socket as shell_socket
import pytest

from declusor import config, contract, testing


def test_connection_state_lifecycle_transitions(
    make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
) -> None:
    """Verify connection lifecycle transitions: CREATED -> CONNECTED -> CLOSED."""

    trans = testing.DummyTransport(incoming_data=b"__DECLUSOR_EOF_test_nonce__\n")

    conn, _ = make_shell_connection(trans)
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


def test_connection_segmented_envelope_streaming(
    make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
) -> None:
    """Verify handshake envelope handles segmented byte streaming properly."""

    trans = testing.DummyTransport(
        incoming_data=[
            b"__DECLUSOR_EOF_",
            b"test_",
            b"nonce__\n",
        ]
    )

    conn, _ = make_shell_connection(trans)
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


def test_write_uses_ephemeral_envelope_framing(
    make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
) -> None:
    """Verify write transmits ephemeral nonce prefix followed by null-delimited payload."""

    connection, trans = make_shell_connection(default_nonce="fixed_nonce")

    connection.write(b"command")
    assert trans.written_bytes == b"fixed_nonce\x00command\x00"


def test_write_translates_transport_errors(
    make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
) -> None:
    """Verify write translates transport errors into domain ConnectionError."""

    trans = testing.DummyTransport()
    trans.simulate_error_on_next_write(config.ConnectionError("transport write failed"))

    connection, _ = make_shell_connection(trans)

    with pytest.raises(config.ConnectionError, match="Failed to write to connection"):
        connection.write(b"command")


def test_write_and_read_ephemeral_envelope(
    make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
) -> None:
    """Verify write transmits ephemeral nonce prefix and read terminates at dynamic envelope."""

    conn, trans = make_shell_connection(framing_mode=config.FramingMode.EPHEMERAL_ENVELOPE)
    conn.write(b"ls -la", nonce="abcdef0123456789")

    assert trans.written_bytes == b"abcdef0123456789\x00ls -la\x00"
    assert conn.current_nonce == "abcdef0123456789"

    envelope = b"__DECLUSOR_EOF_abcdef0123456789__\n"
    trans.push_incoming(b"output_chunk_1\n" + b"output_chunk_2\n" + envelope)

    chunks = list(conn.read())
    assert chunks == [b"output_chunk_1\noutput_chunk_2\n"]


def test_handshake_with_ephemeral_envelope(
    make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
) -> None:
    """Verify handshake in EPHEMERAL_ENVELOPE mode sends helpers and waits for dynamic envelope."""

    conn, trans = make_shell_connection(
        framing_mode=config.FramingMode.EPHEMERAL_ENVELOPE,
        default_nonce="fixed_handshake_nonce",
    )
    trans.push_incoming(b"__DECLUSOR_EOF_fixed_handshake_nonce__\n")
    conn.handshake()

    assert conn.state == contract.ConnectionState.CONNECTED
    assert trans.written_bytes.startswith(b"fixed_handshake_nonce\x00")


def test_connection_invalid_buffer_size(
    make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
) -> None:
    """Verify ShellSocketConnection raises ConnectionError when buffer_size <= 0."""

    with pytest.raises(config.ConnectionError, match="buffer_size must be > 0"):
        make_shell_connection(buffer_size=0)

    with pytest.raises(config.ConnectionError, match="buffer_size must be > 0"):
        make_shell_connection(buffer_size=-1)


def test_connection_renderer_and_timeout_properties(
    make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
) -> None:
    """Verify renderer/profile and timeout property accessors."""

    conn, trans = make_shell_connection(timeout=2.5)
    assert conn.renderer is not None
    assert conn.profile is conn.renderer
    assert conn.timeout == 2.5
    assert trans.timeout == 2.5

    conn.timeout = 5.0
    assert conn.timeout == 5.0
    assert trans.timeout == 5.0


def test_connection_nonce_factory(
    tmp_path: Path,
) -> None:
    """Verify ShellSocketConnection utilizes nonce_factory when fixed_nonce is None."""

    launchers = tmp_path / "launchers"
    launchers.mkdir(exist_ok=True)
    launcher = launchers / "shell_socket_client.sh"
    launcher.write_text("$HOST:$PORT", encoding="utf-8")
    (tmp_path / "helpers").mkdir(exist_ok=True)
    (tmp_path / "modules").mkdir(exist_ok=True)

    trans = testing.DummyTransport(peer_address="127.0.0.1:9000")
    renderer = shell_socket.ShellSocketRenderer()
    fs = contract.PluginFilesystem.from_root(tmp_path)
    files = shell_socket.ShellSocketProcessor(fs)

    counter = 0

    def mock_nonce() -> str:
        nonlocal counter
        counter += 1
        return f"generated_nonce_{counter}"

    conn = shell_socket.ShellSocketConnection(
        trans,
        renderer,
        files,
        fixed_nonce=None,
        nonce_factory=mock_nonce,
    )

    conn.write(b"data1")
    assert trans.written_bytes == b"generated_nonce_1\x00data1\x00"
    assert conn.current_nonce == "generated_nonce_1"

    conn.write(b"data2")
    assert trans.written_bytes == b"generated_nonce_1\x00data1\x00generated_nonce_2\x00data2\x00"
    assert conn.current_nonce == "generated_nonce_2"
