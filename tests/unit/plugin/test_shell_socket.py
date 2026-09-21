from pathlib import Path
from unittest.mock import MagicMock

from declusor import connection, contract
from declusor.plugin import ShellSocketPlugin


def test_build_runtime_renders_configured_client_script(tmp_path: Path) -> None:
    """The runtime must render the script from the selected client config."""

    client_path = tmp_path / "client.sh"
    client_path.write_text("connect $HOST:$PORT ack=$ACKNOWLEDGE", encoding="utf-8")
    client_config = contract.ClientConfig(
        kind=ShellSocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={"client_path": client_path},
    )

    runtime = ShellSocketPlugin.build_runtime(client_config)

    assert runtime.client_script.startswith("connect 127.0.0.1:9000 ack=\\x")


def test_build_runtime_creates_shell_socket_connection(tmp_path: Path) -> None:
    """The runtime must hide shell-socket connection construction."""

    client_path = tmp_path / "client.sh"
    client_path.write_text("$HOST:$PORT", encoding="utf-8")
    client_config = contract.ClientConfig(
        kind=ShellSocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={"client_path": client_path},
    )
    socket_connection = MagicMock()
    socket_connection.getpeername.return_value = ("127.0.0.1", 9000)

    runtime = ShellSocketPlugin.build_runtime(client_config)
    client_connection = runtime.create_connection(socket_connection)

    assert isinstance(client_connection, connection.ShellSocketConnection)
