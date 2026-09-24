from pathlib import Path
from socket import socket
from typing import cast

import py_socket
import pytest

from declusor import config, contract
from declusor.testing import DummySocket


def test_build_runtime_renders_configured_client_script(tmp_path: Path) -> None:
    """Verify PySocketPlugin.build_runtime renders launcher script with host, port, and ACK."""
    launcher = tmp_path / "py_socket_client.py"
    launcher.write_text("HOST = '$HOST'\nPORT = int('$PORT')\nACK = bytes.fromhex('$ACKNOWLEDGE')")

    client_config = contract.ClientConfig(
        kind=py_socket.PySocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={
            "launcher_path": launcher,
            "helpers_dir": tmp_path / "helpers",
            "modules_dir": tmp_path / "modules",
        },
    )

    runtime = py_socket.PySocketPlugin.build_runtime(client_config)
    assert "127.0.0.1" in runtime.client_script
    assert "9000" in runtime.client_script


def test_build_runtime_creates_py_socket_connection(tmp_path: Path) -> None:
    """Verify runtime creates a valid PySocketConnection instance for connected sockets."""
    launcher = tmp_path / "py_socket_client.py"
    launcher.write_text("HOST = '$HOST'\nPORT = int('$PORT')\nACK = bytes.fromhex('$ACKNOWLEDGE')")

    client_config = contract.ClientConfig(
        kind=py_socket.PySocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={
            "launcher_path": launcher,
            "helpers_dir": tmp_path / "helpers",
            "modules_dir": tmp_path / "modules",
        },
    )

    runtime = py_socket.PySocketPlugin.build_runtime(client_config)
    dummy_sock = DummySocket()
    conn = runtime.create_connection(cast(socket, dummy_sock))
    assert isinstance(conn, py_socket.PySocketConnection)


def test_validate_passes_when_launcher_exists(tmp_path: Path) -> None:
    """Verify plugin configuration validation succeeds when launcher file exists."""
    launcher = tmp_path / "py_socket_client.py"
    launcher.write_text("# launcher")

    client_config = contract.ClientConfig(
        kind=py_socket.PySocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={"launcher_path": launcher},
    )

    py_socket.PySocketPlugin.validate(client_config)


def test_validate_raises_when_launcher_missing(tmp_path: Path) -> None:
    """Verify plugin configuration validation raises ParserError when launcher file is missing."""
    client_config = contract.ClientConfig(
        kind=py_socket.PySocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={"launcher_path": tmp_path / "nonexistent.py"},
    )

    with pytest.raises(config.ParserError, match="Client launcher file does not exist"):
        py_socket.PySocketPlugin.validate(client_config)
