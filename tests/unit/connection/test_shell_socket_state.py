from pathlib import Path
from unittest.mock import MagicMock

import pytest

from declusor import config, connection


def _create_test_connection(tmp_path: Path, mock_socket: MagicMock) -> connection.ShellSocketConnection:
    client_path = tmp_path / "client.sh"
    client_path.write_text("$HOST:$PORT", encoding="utf-8")

    profile = connection.ShellSocketProfile(
        name="test",
        ack_server_raw=b"\x00",
        ack_client_raw=b"valid_ack_32_bytes_long_sentinel",
    )
    files = connection.ShellSocketFileStore(
        client_path,
        config.DataPaths.from_root(tmp_path),
        (".sh",),
        (".sh",),
    )
    return connection.ShellSocketConnection(mock_socket, profile, files)


def test_connection_state_lifecycle_transitions(tmp_path: Path) -> None:
    """Connection must transition from CREATED to CONNECTED and CLOSED."""

    mock_socket = MagicMock()
    mock_socket.recv.return_value = b"valid_ack_32_bytes_long_sentinel"

    conn = _create_test_connection(tmp_path, mock_socket)
    assert conn.state == connection.ConnectionState.CREATED

    conn.initialize()
    assert conn.state == connection.ConnectionState.CONNECTED

    conn.close()
    assert conn.state == connection.ConnectionState.CLOSED

    # Calling close again must be idempotent and not fail
    conn.close()
    assert conn.state == connection.ConnectionState.CLOSED


def test_connection_segmented_ack_streaming(tmp_path: Path) -> None:
    """Initialize must handle segmented TCP packet delivery of ACK."""

    mock_socket = MagicMock()
    # Deliver the 32-byte ACK across 3 fragmented TCP reads
    mock_socket.recv.side_effect = [
        b"valid_ack_",
        b"32_bytes_",
        b"long_sentinel",
    ]

    conn = _create_test_connection(tmp_path, mock_socket)
    conn.initialize()
    assert conn.state == connection.ConnectionState.CONNECTED


def test_initialize_fails_on_closed_connection(tmp_path: Path) -> None:
    """Cannot initialize an already closed connection."""

    mock_socket = MagicMock()
    conn = _create_test_connection(tmp_path, mock_socket)
    conn.close()

    with pytest.raises(config.ConnectionFailure, match="Cannot initialize a closed connection"):
        conn.initialize()
