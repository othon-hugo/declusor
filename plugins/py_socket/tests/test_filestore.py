"""Unit tests for PySocketFileStore."""

from pathlib import Path

import py_socket
import pytest

from declusor import config


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
