from pathlib import Path

import pytest

from declusor import config
from declusor.util import storage


def test_load_file_success(tmp_path: Path) -> None:
    """Verify loading existing file content as bytes."""
    target = tmp_path / "payload.bin"
    target.write_bytes(b"payload content")

    content = storage.load_file(target)
    assert content == b"payload content"


def test_load_file_missing_raises_invalid_operation(tmp_path: Path) -> None:
    """Verify missing file raises InvalidOperation."""
    missing = tmp_path / "nonexistent.bin"
    with pytest.raises(config.InvalidOperation, match="does not exist"):
        storage.load_file(missing)


def test_load_file_directory_raises_invalid_operation(tmp_path: Path) -> None:
    """Verify directory path raises InvalidOperation."""
    directory = tmp_path / "subdir"
    directory.mkdir()
    with pytest.raises(config.InvalidOperation, match="is not a file"):
        storage.load_file(directory)


def test_try_load_file_success_and_failure(tmp_path: Path) -> None:
    """Verify try_load_file returns bytes on success, None on failure."""
    target = tmp_path / "payload.bin"
    target.write_bytes(b"data")

    assert storage.try_load_file(target) == b"data"
    assert storage.try_load_file(tmp_path / "missing.bin") is None


def test_ensure_file_exists(tmp_path: Path) -> None:
    """Verify ensure_file_exists resolves and returns Path."""
    target = tmp_path / "valid.txt"
    target.write_text("ok")

    resolved = storage.ensure_file_exists(target)
    assert resolved == target.resolve()


def test_ensure_directory_exists(tmp_path: Path) -> None:
    """Verify ensure_directory_exists resolves Path or raises."""
    subdir = tmp_path / "valid_dir"
    subdir.mkdir()

    assert storage.ensure_directory_exists(subdir) == subdir.resolve()

    missing = tmp_path / "missing_dir"
    with pytest.raises(config.InvalidOperation, match="does not exist"):
        storage.ensure_directory_exists(missing)

    file_as_dir = tmp_path / "file.txt"
    file_as_dir.write_text("not a dir")
    with pytest.raises(config.InvalidOperation, match="is not a directory"):
        storage.ensure_directory_exists(file_as_dir)
