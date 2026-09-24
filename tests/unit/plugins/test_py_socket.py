from pathlib import Path
from socket import socket
from typing import cast

import pytest

from declusor import config, contract
from plugins import py_socket
from tests.testing import DummyClientFileStore, DummySocket

# ---------------------------------------------------------------------------
# Profile Tests
# ---------------------------------------------------------------------------


def test_py_socket_profile_render_operation_command_exec_file() -> None:
    """Verify EXEC_FILE opcode renders execute_base64_encoded_value call."""

    profile = py_socket.DEFAULT_PY_SOCKET
    rendered = profile.render_operation_command(config.OperationCode.EXEC_FILE, "AAAA==")
    assert rendered == "execute_base64_encoded_value('AAAA==')"


def test_py_socket_profile_render_operation_command_store_file() -> None:
    """Verify STORE_FILE opcode renders store_base64_encoded_value call with destination path."""

    profile = py_socket.DEFAULT_PY_SOCKET
    rendered = profile.render_operation_command(config.OperationCode.STORE_FILE, "AAAA==", "/tmp/out")
    assert rendered == "store_base64_encoded_value('AAAA==', '/tmp/out')"


def test_py_socket_profile_supported_functions_are_immutable() -> None:
    """Verify supported functions mapping in PySocketProfile cannot be modified."""

    profile = py_socket.PySocketProfile(name="test", ack_server_raw=b"\x00", ack_client_raw=b"\xab" * 32)
    with pytest.raises(TypeError):
        profile._supported_functions[config.OperationCode.EXEC_FILE] = "changed"  # type: ignore[index]


# ---------------------------------------------------------------------------
# FileStore Tests
# ---------------------------------------------------------------------------


def test_py_socket_file_store_load_library_returns_concatenated_helpers(tmp_path: Path) -> None:
    """Verify PySocketFileStore concatenates all helper library scripts."""

    helpers = tmp_path / "helpers"
    helpers.mkdir(parents=True)
    (helpers / "a.py").write_bytes(b"# helper a")
    (helpers / "b.py").write_bytes(b"# helper b")

    store = py_socket.PySocketFileStore(tmp_path / "client.py", helpers, tmp_path / "modules")
    assert store.load_library() == b"# helper a\n\n# helper b"


def test_py_socket_file_store_load_library_returns_empty_when_no_helpers(tmp_path: Path) -> None:
    """Verify PySocketFileStore returns empty bytes when helpers directory is missing or empty."""

    store = py_socket.PySocketFileStore(tmp_path / "client.py", tmp_path / "helpers", tmp_path / "modules")
    assert store.load_library() == b""


def test_py_socket_file_store_load_module_reads_module(tmp_path: Path) -> None:
    """Verify PySocketFileStore reads module contents from the modules directory."""

    modules = tmp_path / "modules"
    modules.mkdir(parents=True)
    (modules / "info.py").write_bytes(b"# info module")

    store = py_socket.PySocketFileStore(tmp_path / "client.py", tmp_path / "helpers", modules)
    assert store.load_module("info.py") == b"# info module"


def test_py_socket_file_store_load_module_rejects_traversal_and_wrong_extension(tmp_path: Path) -> None:
    """Verify load_module rejects path traversal escapes and unsupported file extensions."""

    modules = tmp_path / "modules"
    modules.mkdir(parents=True)
    (tmp_path / "outside.py").write_bytes(b"outside")

    store = py_socket.PySocketFileStore(tmp_path / "client.py", tmp_path / "helpers", modules)

    with pytest.raises(config.InvalidOperation):
        store.load_module("../outside.py")

    with pytest.raises(config.InvalidOperation):
        store.load_module("bad.sh")


# ---------------------------------------------------------------------------
# Connection Protocol Tests
# ---------------------------------------------------------------------------


def test_py_socket_connection_write_sends_null_delimited_frame(
    dummy_file_store: DummyClientFileStore,
) -> None:
    """Verify PySocketConnection transmits data with null byte framing."""
    dummy_sock = DummySocket(incoming_bytes=b"\x00")
    profile = py_socket.PySocketProfile(name="test", ack_server_raw=b"\x00", ack_client_raw=b"\xab" * 32)

    conn = py_socket.PySocketConnection(cast(socket, dummy_sock), profile, dummy_file_store)
    conn.write(b"data")

    assert dummy_sock.sendall_calls == [b"data\x00"]
    assert dummy_sock.recv_calls == [len(b"\x00")]


def test_py_socket_connection_close_is_idempotent(
    dummy_file_store: DummyClientFileStore,
) -> None:
    """Verify closing PySocketConnection multiple times is idempotent."""
    dummy_sock = DummySocket()
    profile = py_socket.PySocketProfile(name="test", ack_server_raw=b"\x00", ack_client_raw=b"\xab" * 32)

    conn = py_socket.PySocketConnection(cast(socket, dummy_sock), profile, dummy_file_store)
    conn.close()
    conn.close()

    assert dummy_sock.close_calls == 1
    assert dummy_sock.closed is True


# ---------------------------------------------------------------------------
# Plugin & Runtime Tests
# ---------------------------------------------------------------------------


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
