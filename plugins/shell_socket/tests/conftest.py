from collections.abc import Callable
from pathlib import Path

import declusor_shell_socket as shell_socket
import pytest

from declusor import config, contract, testing


@pytest.fixture
def make_shell_connection(
    tmp_path: Path,
) -> Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]]:
    """Helper factory for creating configured ShellSocketConnection instances."""

    def _create_connection(
        transport_connection: testing.DummyTransport | None = None,
        ack: bytes = b"ack",
        framing_mode: config.FramingMode = config.FramingMode.SENTINEL,
        default_nonce: str | None = None,
    ) -> tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]:
        launchers = tmp_path / "launchers"
        launchers.mkdir(exist_ok=True)
        launcher = launchers / "shell_socket_client.sh"
        launcher.write_text("$HOST:$PORT", encoding="utf-8")

        helpers = tmp_path / "helpers"
        helpers.mkdir(exist_ok=True)
        modules = tmp_path / "modules"
        modules.mkdir(exist_ok=True)

        trans = transport_connection or testing.DummyTransport(peer_address="127.0.0.1:9000")
        profile = shell_socket.ShellSocketProfile(
            name="test",
            ack_server_raw=b"\x00",
            ack_client_raw=ack,
            _framing_mode=framing_mode,
            _default_nonce=default_nonce,
        )
        fs = contract.PluginFilesystem.from_root(tmp_path)
        files = shell_socket.ShellSocketProcessor(fs)

        return shell_socket.ShellSocketConnection(trans, profile, files), trans

    return _create_connection
