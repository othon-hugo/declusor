from pathlib import Path
from unittest.mock import MagicMock

import pytest

from declusor import config, connection


def _create_connection(tmp_path: Path, socket_connection: MagicMock) -> connection.ShellSocketConnection:
    """Create a shell-socket connection backed by a mocked socket."""

    client_path = tmp_path / "client.sh"
    client_path.write_text("$HOST:$PORT", encoding="utf-8")
    socket_connection.getpeername.return_value = ("127.0.0.1", 9000)
    profile = connection.ShellSocketProfile(
        name="test",
        client_path=client_path,
        ack_server_raw=b"\x00",
        ack_client_raw=b"ack",
        allowed_payload_extensions=(".sh",),
        allowed_library_extensions=(".sh",),
    )

    return connection.ShellSocketConnection(socket_connection, profile)


def test_write_uses_sendall_for_payload_and_ack(tmp_path: Path) -> None:
    """Writing a message must transmit the payload and ACK completely."""

    socket_connection = MagicMock()
    session = _create_connection(tmp_path, socket_connection)

    session.write(b"command")

    assert socket_connection.sendall.call_args_list == [
        ((b"command",),),
        ((b"\x00",),),
    ]


@pytest.mark.parametrize("error", [OSError("broken pipe"), TimeoutError("timed out")])
def test_write_translates_transport_errors(tmp_path: Path, error: BaseException) -> None:
    """Transport errors during writing must become ConnectionFailure."""

    socket_connection = MagicMock()
    socket_connection.sendall.side_effect = error
    session = _create_connection(tmp_path, socket_connection)

    with pytest.raises(config.ConnectionFailure) as raised:
        session.write(b"command")

    assert raised.value.__cause__ is error
