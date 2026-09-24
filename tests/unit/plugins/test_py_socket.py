from pathlib import Path
from unittest.mock import MagicMock

import pytest

from declusor import config, contract
from plugins.py_socket import (
    DEFAULT_PY_SOCKET,
    PySocketConnection,
    PySocketFileStore,
    PySocketPlugin,
    PySocketProfile,
)

# ---------------------------------------------------------------------------
# Profile Tests
# ---------------------------------------------------------------------------


def test_py_socket_profile_render_operation_command_exec_file() -> None:
    profile = DEFAULT_PY_SOCKET
    rendered = profile.render_operation_command(config.OperationCode.EXEC_FILE, "AAAA==")
    assert rendered == "execute_base64_encoded_value('AAAA==')"


def test_py_socket_profile_render_operation_command_store_file() -> None:
    profile = DEFAULT_PY_SOCKET
    rendered = profile.render_operation_command(config.OperationCode.STORE_FILE, "AAAA==", "/tmp/out")
    assert rendered == "store_base64_encoded_value('AAAA==', '/tmp/out')"


def test_py_socket_profile_supported_functions_are_immutable() -> None:
    profile = PySocketProfile(name="test", ack_server_raw=b"\x00", ack_client_raw=b"\xab" * 32)
    with pytest.raises(TypeError):
        profile._supported_functions[config.OperationCode.EXEC_FILE] = "changed"  # type: ignore[index]


# ---------------------------------------------------------------------------
# FileStore Tests
# ---------------------------------------------------------------------------


def test_py_socket_file_store_load_library_returns_concatenated_helpers(tmp_path: Path) -> None:
    helpers = tmp_path / "helpers"
    helpers.mkdir(parents=True)
    (helpers / "a.py").write_bytes(b"# helper a")
    (helpers / "b.py").write_bytes(b"# helper b")

    store = PySocketFileStore(tmp_path / "client.py", helpers, tmp_path / "modules")
    assert store.load_library() == b"# helper a\n\n# helper b"


def test_py_socket_file_store_load_library_returns_empty_when_no_helpers(tmp_path: Path) -> None:
    store = PySocketFileStore(tmp_path / "client.py", tmp_path / "helpers", tmp_path / "modules")
    assert store.load_library() == b""


def test_py_socket_file_store_load_module_reads_module(tmp_path: Path) -> None:
    modules = tmp_path / "modules"
    modules.mkdir(parents=True)
    (modules / "info.py").write_bytes(b"# info module")

    store = PySocketFileStore(tmp_path / "client.py", tmp_path / "helpers", modules)
    assert store.load_module("info.py") == b"# info module"


def test_py_socket_file_store_load_module_rejects_traversal_and_wrong_extension(tmp_path: Path) -> None:
    modules = tmp_path / "modules"
    modules.mkdir(parents=True)
    (tmp_path / "outside.py").write_bytes(b"outside")

    store = PySocketFileStore(tmp_path / "client.py", tmp_path / "helpers", modules)

    with pytest.raises(config.InvalidOperation):
        store.load_module("../outside.py")

    with pytest.raises(config.InvalidOperation):
        store.load_module("bad.sh")


# ---------------------------------------------------------------------------
# Connection Protocol Tests
# ---------------------------------------------------------------------------


def test_py_socket_connection_write_sends_null_delimited_frame() -> None:
    mock_socket = MagicMock()
    profile = PySocketProfile(name="test", ack_server_raw=b"\x00", ack_client_raw=b"\xab" * 32)
    mock_files = MagicMock()

    conn = PySocketConnection(mock_socket, profile, mock_files)
    conn.write(b"data")

    mock_socket.sendall.assert_called_once_with(b"data\x00")
    mock_socket.recv.assert_called_once_with(len(b"\x00"))


def test_py_socket_connection_close_is_idempotent() -> None:
    mock_socket = MagicMock()
    profile = PySocketProfile(name="test", ack_server_raw=b"\x00", ack_client_raw=b"\xab" * 32)
    mock_files = MagicMock()

    conn = PySocketConnection(mock_socket, profile, mock_files)
    conn.close()
    conn.close()

    mock_socket.close.assert_called_once()


# ---------------------------------------------------------------------------
# Plugin & Runtime Tests
# ---------------------------------------------------------------------------


def test_build_runtime_renders_configured_client_script(tmp_path: Path) -> None:
    launcher = tmp_path / "py_socket_client.py"
    launcher.write_text("HOST = '$HOST'\nPORT = int('$PORT')\nACK = bytes.fromhex('$ACKNOWLEDGE')")

    client_config = contract.ClientConfig(
        kind=PySocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={
            "launcher_path": launcher,
            "helpers_dir": tmp_path / "helpers",
            "modules_dir": tmp_path / "modules",
        },
    )

    runtime = PySocketPlugin.build_runtime(client_config)
    assert "127.0.0.1" in runtime.client_script
    assert "9000" in runtime.client_script


def test_build_runtime_creates_py_socket_connection(tmp_path: Path) -> None:
    launcher = tmp_path / "py_socket_client.py"
    launcher.write_text("HOST = '$HOST'\nPORT = int('$PORT')\nACK = bytes.fromhex('$ACKNOWLEDGE')")

    client_config = contract.ClientConfig(
        kind=PySocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={
            "launcher_path": launcher,
            "helpers_dir": tmp_path / "helpers",
            "modules_dir": tmp_path / "modules",
        },
    )

    runtime = PySocketPlugin.build_runtime(client_config)
    conn = runtime.create_connection(MagicMock())
    assert isinstance(conn, PySocketConnection)


def test_validate_passes_when_launcher_exists(tmp_path: Path) -> None:
    launcher = tmp_path / "py_socket_client.py"
    launcher.write_text("# launcher")

    client_config = contract.ClientConfig(
        kind=PySocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={"launcher_path": launcher},
    )

    PySocketPlugin.validate(client_config)


def test_validate_raises_when_launcher_missing(tmp_path: Path) -> None:
    client_config = contract.ClientConfig(
        kind=PySocketPlugin.name,
        host="127.0.0.1",
        port=9000,
        options={"launcher_path": tmp_path / "nonexistent.py"},
    )

    with pytest.raises(config.ParserError, match="Client launcher file does not exist"):
        PySocketPlugin.validate(client_config)
