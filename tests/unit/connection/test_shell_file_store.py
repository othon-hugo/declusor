from pathlib import Path

import pytest

from declusor import config, connection, util


def _make_store(tmp_path: Path, *, lib_exts: tuple = (".sh",), mod_exts: tuple = (".sh",)) -> connection.ShellSocketFileStore:
    """Build a ``ShellSocketFileStore`` rooted under ``tmp_path/shell_socket/``."""
    client_path = tmp_path / "shell_socket" / "launchers" / "shell_socket.sh"
    client_path.parent.mkdir(parents=True, exist_ok=True)
    data_paths = config.DataPaths.from_root(tmp_path)
    return connection.ShellSocketFileStore(client_path, data_paths, lib_exts, mod_exts)


def test_load_library_reports_read_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Library read failures must not be silently treated as missing files."""

    helpers_dir = tmp_path / "shell_socket" / "helpers"
    helpers_dir.mkdir(parents=True)
    (helpers_dir / "common.sh").write_bytes(b"echo common")

    store = _make_store(tmp_path)

    def fail_load_file(filepath: str | Path, /) -> bytes:
        raise config.InvalidOperation(f"cannot read {filepath}")

    monkeypatch.setattr(util, "load_file", fail_load_file)

    with pytest.raises(config.ConnectionFailure, match="common.sh"):
        store.load_library()


def test_load_library_returns_non_empty_scripts(tmp_path: Path) -> None:
    """Valid shell libraries must be concatenated in the upload payload."""

    helpers_dir = tmp_path / "shell_socket" / "helpers"
    helpers_dir.mkdir(parents=True)
    (helpers_dir / "common.sh").write_bytes(b"echo common")

    store = _make_store(tmp_path)

    assert store.load_library() == b"echo common"


def test_load_module_reads_only_from_modules_directory(tmp_path: Path) -> None:
    """Explicit module loading must use ``shell_socket/modules`` and its policy."""

    modules_dir = tmp_path / "shell_socket" / "modules"
    modules_dir.mkdir(parents=True)
    (modules_dir / "example.sh").write_bytes(b"echo module")

    store = _make_store(tmp_path)

    assert store.load_module("example.sh") == b"echo module"


def test_load_module_rejects_traversal_and_wrong_extension(tmp_path: Path) -> None:
    """Explicit module loading must reject unsafe or unsupported paths."""

    modules_dir = tmp_path / "shell_socket" / "modules"
    modules_dir.mkdir(parents=True)
    (tmp_path / "outside.txt").write_bytes(b"outside")

    store = _make_store(tmp_path)

    with pytest.raises(config.InvalidOperation):
        store.load_module("../outside.txt")

    with pytest.raises(config.InvalidOperation):
        store.load_module("outside.txt")
