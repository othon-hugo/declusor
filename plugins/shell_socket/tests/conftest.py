from collections.abc import Callable
from pathlib import Path
from socket import socket
from typing import cast

import declusor_shell_socket as shell_socket
import pytest

from declusor import contract, testing


@pytest.fixture
def make_shell_connection(
    tmp_path: Path,
) -> Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummySocket]]:
    """Helper factory for creating configured ShellSocketConnection instances."""

    def _create_connection(
        socket_connection: testing.DummySocket | None = None,
        ack: bytes = b"ack",
    ) -> tuple[shell_socket.ShellSocketConnection, testing.DummySocket]:
        launchers = tmp_path / "launchers"
        launchers.mkdir(exist_ok=True)
        launcher = launchers / "shell_socket_client.sh"
        launcher.write_text("$HOST:$PORT", encoding="utf-8")

        helpers = tmp_path / "helpers"
        helpers.mkdir(exist_ok=True)
        modules = tmp_path / "modules"
        modules.mkdir(exist_ok=True)

        sock = socket_connection or testing.DummySocket(peer_name=("127.0.0.1", 9000))
        profile = shell_socket.ShellSocketProfile(name="test", ack_server_raw=b"\x00", ack_client_raw=ack)
        fs = contract.PluginFilesystem.from_root(tmp_path)
        files = shell_socket.ShellSocketProcessor(fs)

        return shell_socket.ShellSocketConnection(cast(socket, sock), profile, files), sock

    return _create_connection
