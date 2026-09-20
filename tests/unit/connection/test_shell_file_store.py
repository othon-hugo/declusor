from pathlib import Path

import pytest

from declusor import config, connection, util


def test_load_library_reports_read_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Library read failures must not be silently treated as missing files."""

    library = tmp_path / "library"
    library.mkdir()

    library_file = library / "common.sh"
    library_file.write_bytes(b"echo common")

    data_paths = config.DataPaths.from_root(tmp_path)
    store = connection.ShellSocketFileStore(tmp_path / "client.sh", data_paths, (".sh",), (".sh",))

    def fail_load_file(filepath: str | Path, /) -> bytes:
        raise config.InvalidOperation(f"cannot read {filepath}")

    monkeypatch.setattr(util, "load_file", fail_load_file)

    with pytest.raises(config.ConnectionFailure, match="common.sh"):
        store.load_library()


def test_load_library_returns_non_empty_scripts(tmp_path: Path) -> None:
    """Valid shell libraries must be concatenated in the upload payload."""

    library = tmp_path / "library"
    library.mkdir()

    (library / "common.sh").write_bytes(b"echo common")

    data_paths = config.DataPaths.from_root(tmp_path)
    store = connection.ShellSocketFileStore(tmp_path / "client.sh", data_paths, (".sh",), (".sh",))

    assert store.load_library() == b"echo common"


def test_load_module_reads_only_from_modules_directory(tmp_path: Path) -> None:
    """Explicit module loading must use ``data/modules`` and its policy."""

    modules = tmp_path / "modules"
    modules.mkdir()
    (modules / "example.sh").write_bytes(b"echo module")
    data_paths = config.DataPaths.from_root(tmp_path)
    store = connection.ShellSocketFileStore(tmp_path / "client.sh", data_paths, (".sh",), (".sh",))

    assert store.load_module("example.sh") == b"echo module"


def test_load_module_rejects_traversal_and_wrong_extension(tmp_path: Path) -> None:
    """Explicit module loading must reject unsafe or unsupported paths."""

    modules = tmp_path / "modules"
    modules.mkdir()
    (tmp_path / "outside.txt").write_bytes(b"outside")
    data_paths = config.DataPaths.from_root(tmp_path)
    store = connection.ShellSocketFileStore(tmp_path / "client.sh", data_paths, (".sh",), (".sh",))

    with pytest.raises(config.InvalidOperation):
        store.load_module("../outside.txt")

    with pytest.raises(config.InvalidOperation):
        store.load_module("outside.txt")
