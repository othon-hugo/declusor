from pathlib import Path
from socket import socket
from typing import cast

import declusor_shell_socket as shell_socket

from declusor import contract, testing


def test_shell_socket_plugin_metadata() -> None:
    """Verify shell_socket.ShellSocketPlugin metadata properties (name, description, version)."""

    assert shell_socket.ShellSocketPlugin.name == "shell_socket"
    assert shell_socket.ShellSocketPlugin.description != ""
    assert shell_socket.ShellSocketPlugin.version == "1.0.0"


def test_build_runtime_renders_configured_client_script(tmp_path: Path) -> None:
    """Verify shell_socket.ShellSocketPlugin.build_runtime renders client script with substituted parameters."""

    client_path = tmp_path / "client.sh"
    client_path.write_text("connect $HOST:$PORT ack=$ACKNOWLEDGE", encoding="utf-8")
    client_config = contract.ClientConfig(
        kind=shell_socket.ShellSocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={
            "launcher_path": client_path,
            "helpers_dir": tmp_path / "helpers",
            "modules_dir": tmp_path / "modules",
        },
    )

    runtime = shell_socket.ShellSocketPlugin.build_runtime(client_config)
    assert runtime.client_script.startswith("connect 127.0.0.1:9000 ack=\\x")


def test_build_runtime_creates_shell_socket_connection(tmp_path: Path) -> None:
    """Verify runtime creates a valid shell_socket.ShellSocketConnection instance."""

    client_path = tmp_path / "client.sh"
    client_path.write_text("$HOST:$PORT", encoding="utf-8")
    client_config = contract.ClientConfig(
        kind=shell_socket.ShellSocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={
            "launcher_path": client_path,
            "helpers_dir": tmp_path / "helpers",
            "modules_dir": tmp_path / "modules",
        },
    )
    dummy_sock = testing.DummySocket(peer_name=("127.0.0.1", 9000))

    runtime = shell_socket.ShellSocketPlugin.build_runtime(client_config)
    client_connection = runtime.create_connection(cast(socket, dummy_sock))

    assert isinstance(client_connection, shell_socket.ShellSocketConnection)
