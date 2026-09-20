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
    store = connection.ShellSocketFileStore(tmp_path / "client.sh", data_paths, (".sh",))

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
    store = connection.ShellSocketFileStore(tmp_path / "client.sh", data_paths, (".sh",))

    assert store.load_library() == b"echo common"
