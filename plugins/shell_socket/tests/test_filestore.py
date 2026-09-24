from pathlib import Path

import pytest
import shell_socket

from declusor import config, util


def test_load_library_reports_read_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify load_library wraps file reading errors into ConnectionError."""

    helpers = tmp_path / "helpers"
    helpers.mkdir(parents=True)
    (helpers / "common.sh").write_bytes(b"echo common")

    store = shell_socket.ShellSocketFileStore(tmp_path / "client.sh", helpers, tmp_path / "modules")

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

    store = shell_socket.ShellSocketFileStore(tmp_path / "client.sh", helpers, tmp_path / "modules")
    assert store.load_library() == b"echo common"


def test_load_module_reads_only_from_modules_directory(tmp_path: Path) -> None:
    """Verify load_module reads modules from the designated modules directory."""

    modules = tmp_path / "modules"
    modules.mkdir(parents=True)
    (modules / "example.sh").write_bytes(b"echo module")

    store = shell_socket.ShellSocketFileStore(tmp_path / "client.sh", tmp_path / "helpers", modules)
    assert store.load_module("example.sh") == b"echo module"


def test_load_module_rejects_traversal_and_wrong_extension(tmp_path: Path) -> None:
    """Verify load_module rejects path traversal escapes and unauthorized file extensions."""

    modules = tmp_path / "modules"
    modules.mkdir(parents=True)
    (tmp_path / "outside.txt").write_bytes(b"outside")

    store = shell_socket.ShellSocketFileStore(tmp_path / "client.sh", tmp_path / "helpers", modules)

    with pytest.raises(config.InvalidOperation):
        store.load_module("../outside.txt")

    with pytest.raises(config.InvalidOperation):
        store.load_module("outside.txt")
