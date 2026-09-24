from pathlib import Path
from unittest.mock import MagicMock

import pytest

from declusor import config, contract, util
from plugins import shell_socket


def _create_connection(tmp_path: Path, socket_connection: MagicMock, ack: bytes = b"ack") -> ShellSocketConnection:
    launcher = tmp_path / "client.sh"
    launcher.write_text("$HOST:$PORT", encoding="utf-8")
    helpers = tmp_path / "helpers"
    helpers.mkdir(exist_ok=True)
    modules = tmp_path / "modules"
    modules.mkdir(exist_ok=True)

    socket_connection.getpeername.return_value = ("127.0.0.1", 9000)
    profile = ShellSocketProfile(name="test", ack_server_raw=b"\x00", ack_client_raw=ack)
    files = ShellSocketFileStore(launcher, helpers, modules, (".sh",), (".sh",))
    return ShellSocketConnection(socket_connection, profile, files)


# ---------------------------------------------------------------------------
# Profile Tests
# ---------------------------------------------------------------------------


def test_profile_supported_functions_are_immutable() -> None:
    """Verify supported functions mapping in ShellSocketProfile cannot be modified."""

    profile = ShellSocketProfile(name="test", ack_server_raw=b"\x00", ack_client_raw=b"ack")
    with pytest.raises(TypeError):
        profile._supported_functions[config.OperationCode.EXEC_FILE] = "changed"  # type: ignore[index]


def test_profile_render_operation_command() -> None:
    """Verify render_operation_command produces correct shell function invocations."""

    profile = DEFAULT_SHELL_SOCKET
    rendered_exec = profile.render_operation_command(config.OperationCode.EXEC_FILE, "payload==")
    assert rendered_exec is not None
    assert "execute_base64_encoded_value payload==" in rendered_exec

    rendered_store = profile.render_operation_command(config.OperationCode.STORE_FILE, "payload==", "/tmp/f")
    assert rendered_store is not None
    assert "store_base64_encoded_value payload== /tmp/f" in rendered_store


# ---------------------------------------------------------------------------
# FileStore Tests
# ---------------------------------------------------------------------------


def test_load_library_reports_read_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify load_library wraps file reading errors into ConnectionError."""

    helpers = tmp_path / "helpers"
    helpers.mkdir(parents=True)
    (helpers / "common.sh").write_bytes(b"echo common")

    store = ShellSocketFileStore(tmp_path / "client.sh", helpers, tmp_path / "modules")

    def fail_load_file(filepath: str | Path, /) -> bytes:
        raise config.InvalidOperation(f"cannot read {filepath}")

    monkeypatch.setattr(util, "load_file", fail_load_file)

    with pytest.raises(config.ConnectionError, match="common.sh"):
        store.load_library()


def test_load_library_returns_non_empty_scripts(tmp_path: Path) -> None:
    """Verify load_library concatenates valid shell scripts from helpers directory."""

    helpers = tmp_path / "helpers"
    helpers.mkdir(parents=True)
    (helpers / "common.sh").write_bytes(b"echo common")

    store = ShellSocketFileStore(tmp_path / "client.sh", helpers, tmp_path / "modules")
    assert store.load_library() == b"echo common"


def test_load_module_reads_only_from_modules_directory(tmp_path: Path) -> None:
    """Verify load_module reads modules from the designated modules directory."""

    modules = tmp_path / "modules"
    modules.mkdir(parents=True)
    (modules / "example.sh").write_bytes(b"echo module")

    store = ShellSocketFileStore(tmp_path / "client.sh", tmp_path / "helpers", modules)
    assert store.load_module("example.sh") == b"echo module"


def test_load_module_rejects_traversal_and_wrong_extension(tmp_path: Path) -> None:
    """Verify load_module rejects path traversal escapes and unauthorized file extensions."""

    modules = tmp_path / "modules"
    modules.mkdir(parents=True)
    (tmp_path / "outside.txt").write_bytes(b"outside")

    store = ShellSocketFileStore(tmp_path / "client.sh", tmp_path / "helpers", modules)

    with pytest.raises(config.InvalidOperation):
        store.load_module("../outside.txt")

    with pytest.raises(config.InvalidOperation):
        store.load_module("outside.txt")


# ---------------------------------------------------------------------------
# Connection Lifecycle & Protocol Tests
# ---------------------------------------------------------------------------


def test_connection_state_lifecycle_transitions(tmp_path: Path) -> None:
    """Verify connection lifecycle transitions: CREATED -> CONNECTED -> CLOSED."""

    mock_socket = MagicMock()
    mock_socket.recv.return_value = b"valid_ack_32_bytes_long_sentinel"

    conn = _create_connection(tmp_path, mock_socket, ack=b"valid_ack_32_bytes_long_sentinel")
    assert conn.state == contract.ConnectionState.CREATED

    conn.initialize()
    assert conn.state == contract.ConnectionState.CONNECTED

    conn.close()
    assert conn.state == contract.ConnectionState.CLOSED

    # Calling close again must be idempotent
    conn.close()
    assert conn.state == contract.ConnectionState.CLOSED


def test_connection_segmented_ack_streaming(tmp_path: Path) -> None:
    """Verify ACK validation handles segmented byte streaming properly."""

    mock_socket = MagicMock()
    mock_socket.recv.side_effect = [
        b"\x00",
        b"valid_ack_",
        b"32_bytes_",
        b"long_sentinel",
    ]

    conn = _create_connection(tmp_path, mock_socket, ack=b"valid_ack_32_bytes_long_sentinel")
    conn.initialize()
    assert conn.state == contract.ConnectionState.CONNECTED


def test_initialize_fails_on_closed_connection(tmp_path: Path) -> None:
    """Verify initialize raises ConnectionError when connection is already closed."""

    mock_socket = MagicMock()
    conn = _create_connection(tmp_path, mock_socket)
    conn.close()

    with pytest.raises(config.ConnectionError, match="Cannot initialize a closed connection"):
        conn.initialize()


def test_write_uses_sendall_for_payload_and_ack(tmp_path: Path) -> None:
    """Verify write uses sendall to transmit payload followed by null byte framing."""

    socket_connection = MagicMock()
    connection = _create_connection(tmp_path, socket_connection)

    connection.write(b"command")
    assert socket_connection.sendall.call_args_list == [((b"command",),), ((b"\x00",),)]


@pytest.mark.parametrize("error", [OSError("broken pipe"), TimeoutError("timed out")])
def test_write_translates_transport_errors(tmp_path: Path, error: BaseException) -> None:
    """Verify write translates socket transport errors into domain ConnectionError."""

    socket_connection = MagicMock()
    socket_connection.sendall.side_effect = error

    connection = _create_connection(tmp_path, socket_connection)

    with pytest.raises(config.ConnectionError) as raised:
        connection.write(b"command")

    assert raised.value.__cause__ is error


# ---------------------------------------------------------------------------
# Plugin & Runtime Tests
# ---------------------------------------------------------------------------


def test_shell_socket_plugin_metadata() -> None:
    """Verify ShellSocketPlugin metadata properties (name, description, version)."""

    assert ShellSocketPlugin.name == "shell_socket"
    assert ShellSocketPlugin.description != ""
    assert ShellSocketPlugin.version == "1.0.0"


def test_build_runtime_renders_configured_client_script(tmp_path: Path) -> None:
    """Verify ShellSocketPlugin.build_runtime renders client script with substituted parameters."""

    client_path = tmp_path / "client.sh"
    client_path.write_text("connect $HOST:$PORT ack=$ACKNOWLEDGE", encoding="utf-8")
    client_config = contract.ClientConfig(
        kind=ShellSocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={
            "launcher_path": client_path,
            "helpers_dir": tmp_path / "helpers",
            "modules_dir": tmp_path / "modules",
        },
    )

    runtime = ShellSocketPlugin.build_runtime(client_config)
    assert runtime.client_script.startswith("connect 127.0.0.1:9000 ack=\\x")


def test_build_runtime_creates_shell_socket_connection(tmp_path: Path) -> None:
    """Verify runtime creates a valid ShellSocketConnection instance."""

    client_path = tmp_path / "client.sh"
    client_path.write_text("$HOST:$PORT", encoding="utf-8")
    client_config = contract.ClientConfig(
        kind=ShellSocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={
            "launcher_path": client_path,
            "helpers_dir": tmp_path / "helpers",
            "modules_dir": tmp_path / "modules",
        },
    )
    socket_connection = MagicMock()
    socket_connection.getpeername.return_value = ("127.0.0.1", 9000)

    runtime = ShellSocketPlugin.build_runtime(client_config)
    client_connection = runtime.create_connection(socket_connection)

    assert isinstance(client_connection, ShellSocketConnection)
