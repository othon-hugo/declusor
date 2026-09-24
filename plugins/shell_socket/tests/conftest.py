from collections.abc import Callable
from pathlib import Path
from socket import socket
from typing import cast

import declusor_shell_socket as shell_socket
import pytest

from declusor.testing import DummySocket


@pytest.fixture
def make_shell_connection(
    tmp_path: Path,
) -> Callable[..., tuple[shell_socket.ShellSocketConnection, DummySocket]]:
    """Helper factory for creating configured ShellSocketConnection instances."""

    def _create_connection(
        socket_connection: DummySocket | None = None,
        ack: bytes = b"ack",
    ) -> tuple[shell_socket.ShellSocketConnection, DummySocket]:
        launcher = tmp_path / "client.sh"
        launcher.write_text("$HOST:$PORT", encoding="utf-8")
        helpers = tmp_path / "helpers"
        helpers.mkdir(exist_ok=True)
        modules = tmp_path / "modules"
        modules.mkdir(exist_ok=True)

        sock = socket_connection or DummySocket(peer_name=("127.0.0.1", 9000))
        profile = shell_socket.ShellSocketProfile(name="test", ack_server_raw=b"\x00", ack_client_raw=ack)
        files = shell_socket.ShellSocketFileStore(launcher, helpers, modules, (".sh",), (".sh",))
        return shell_socket.ShellSocketConnection(cast(socket, sock), profile, files), sock

    return _create_connection
