from pathlib import Path
from unittest.mock import MagicMock

import pytest

from declusor import config, connection
from declusor.connection.py_socket import PySocketFileStore, PySocketProfile

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_profile() -> PySocketProfile:
    return connection.PySocketProfile(
        name="test",
        ack_server_raw=b"\x00",
        ack_client_raw=b"\xab" * 32,
    )


def _make_store(tmp_path: Path, *, lib_exts: tuple = (".py",), mod_exts: tuple = (".py",)) -> PySocketFileStore:
    """Build a ``PySocketFileStore`` rooted under ``tmp_path/py_socket/``."""
    client_path = tmp_path / "py_socket" / "launchers" / "py_socket_client.py"
    client_path.parent.mkdir(parents=True, exist_ok=True)
    data_paths = config.DataPaths.from_root(tmp_path)
    return PySocketFileStore(client_path, data_paths, lib_exts, mod_exts)


# ---------------------------------------------------------------------------
# PySocketProfile tests
# ---------------------------------------------------------------------------


def test_py_socket_profile_render_operation_command_exec_file() -> None:
    """EXEC_FILE opcode must render the correct Python function call string."""

    profile = _make_profile()

    result = profile.render_operation_command(config.OperationCode.EXEC_FILE, "AAAA==")

    assert result == "execute_base64_encoded_value('AAAA==')"


def test_py_socket_profile_render_operation_command_store_file() -> None:
    """STORE_FILE opcode must render the correct Python function call string with two arguments."""

    profile = _make_profile()

    result = profile.render_operation_command(config.OperationCode.STORE_FILE, "AAAA==", "/tmp/out")

    assert result == "store_base64_encoded_value('AAAA==', '/tmp/out')"


def test_py_socket_profile_supported_functions_are_immutable() -> None:
    """A frozen profile must not expose a mutable function mapping."""

    profile = _make_profile()

    with pytest.raises(TypeError):
        profile._supported_functions["new"] = "x"  # type: ignore[index]


# ---------------------------------------------------------------------------
# PySocketFileStore tests
# ---------------------------------------------------------------------------


def test_py_socket_file_store_load_library_returns_concatenated_helpers(tmp_path: Path) -> None:
    """Valid Python helpers must be sorted and concatenated with double newlines."""

    helpers_dir = tmp_path / "py_socket" / "helpers"
    helpers_dir.mkdir(parents=True)
    (helpers_dir / "a.py").write_bytes(b"# helper a")
    (helpers_dir / "b.py").write_bytes(b"# helper b")

    store = _make_store(tmp_path)

    assert store.load_library() == b"# helper a\n\n# helper b"


def test_py_socket_file_store_load_library_returns_empty_when_no_helpers(tmp_path: Path) -> None:
    """An absent helpers directory must produce empty bytes, not an error."""

    store = _make_store(tmp_path)

    assert store.load_library() == b""


def test_py_socket_file_store_load_module_reads_module(tmp_path: Path) -> None:
    """A valid module inside the modules directory must be returned verbatim."""

    modules_dir = tmp_path / "py_socket" / "modules"
    modules_dir.mkdir(parents=True)
    (modules_dir / "info.py").write_bytes(b"# info module")

    store = _make_store(tmp_path)

    assert store.load_module("info.py") == b"# info module"


def test_py_socket_file_store_load_module_rejects_traversal_and_wrong_extension(tmp_path: Path) -> None:
    """Path-traversal attempts and unsupported extensions must raise InvalidOperation."""

    modules_dir = tmp_path / "py_socket" / "modules"
    modules_dir.mkdir(parents=True)

    store = _make_store(tmp_path)

    with pytest.raises(config.InvalidOperation):
        store.load_module("../escape.py")

    with pytest.raises(config.InvalidOperation):
        store.load_module("bad.sh")


# ---------------------------------------------------------------------------
# PySocketConnection tests
# ---------------------------------------------------------------------------


def test_py_socket_connection_write_sends_null_delimited_frame(tmp_path: Path) -> None:
    """write() must append a null byte and deliver the full frame via sendall."""

    mock_socket = MagicMock()
    profile = _make_profile()
    mock_files = MagicMock()

    conn = connection.PySocketConnection(mock_socket, profile, mock_files)
    conn.write(b"data")

    mock_socket.sendall.assert_called_once_with(b"data\x00")


def test_py_socket_connection_close_is_idempotent(tmp_path: Path) -> None:
    """Calling close() twice must close the underlying socket exactly once."""

    mock_socket = MagicMock()
    profile = _make_profile()
    mock_files = MagicMock()

    conn = connection.PySocketConnection(mock_socket, profile, mock_files)

    conn.close()
    mock_socket.close.side_effect = OSError("already closed")
    conn.close()  # must not raise

    mock_socket.close.assert_called_once()
