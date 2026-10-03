"""Unit tests for filesystem storage utility functions."""

import os
from pathlib import Path

import pytest

from declusor import config
from declusor.util import storage


class TestLoadFile:
    """Tests for load_file."""

    def test_load_file__existing_file__returns_file_bytes(self, tmp_path: Path) -> None:
        """Verify load_file reads and returns full content of an existing file."""

        target = tmp_path / "payload.bin"
        target.write_bytes(b"payload content")

        content = storage.load_file(target)

        assert content == b"payload content"

    def test_load_file__empty_file__returns_empty_bytes(self, tmp_path: Path) -> None:
        """Verify load_file returns empty bytes when reading an empty file."""

        target = tmp_path / "empty.bin"
        target.touch()

        content = storage.load_file(target)

        assert content == b""

    def test_load_file__string_filepath__returns_file_bytes(self, tmp_path: Path) -> None:
        """Verify load_file accepts string path representations."""

        target = tmp_path / "script.py"
        target.write_bytes(b"print('hello')")

        content = storage.load_file(str(target))

        assert content == b"print('hello')"

    def test_load_file__missing_file__raises_storage_validation_error(self, tmp_path: Path) -> None:
        """Verify load_file raises StorageValidationError when file does not exist."""

        missing = tmp_path / "nonexistent.bin"

        with pytest.raises(config.StorageValidationError, match="does not exist") as exc_info:
            storage.load_file(missing)

        assert exc_info.value.path == missing.resolve()

    def test_load_file__directory_path__raises_storage_validation_error(self, tmp_path: Path) -> None:
        """Verify load_file raises StorageValidationError when path points to a directory."""

        directory = tmp_path / "subdir"
        directory.mkdir()

        with pytest.raises(config.StorageValidationError, match="is not a file") as exc_info:
            storage.load_file(directory)

        assert exc_info.value.path == directory.resolve()

    def test_load_file__unreadable_file__raises_storage_validation_error_with_cause(self, tmp_path: Path) -> None:
        """Verify load_file wraps unreadable file OSError into StorageValidationError with cause."""

        target = tmp_path / "unreadable.bin"
        target.write_bytes(b"secret")
        os.chmod(target, 0)

        try:
            with pytest.raises(config.StorageValidationError, match="could not read file") as exc_info:
                storage.load_file(target)

            assert exc_info.value.path == target.resolve()
            assert isinstance(exc_info.value.__cause__, OSError)
        finally:
            os.chmod(target, 0o600)


class TestTryLoadFile:
    """Tests for try_load_file."""

    def test_try_load_file__existing_file__returns_file_bytes(self, tmp_path: Path) -> None:
        """Verify try_load_file returns file bytes on readable existing file."""

        target = tmp_path / "payload.bin"
        target.write_bytes(b"data")

        assert storage.try_load_file(target) == b"data"

    def test_try_load_file__empty_file__returns_empty_bytes(self, tmp_path: Path) -> None:
        """Verify try_load_file returns empty bytes when file is empty."""

        target = tmp_path / "empty.bin"
        target.touch()

        assert storage.try_load_file(target) == b""

    def test_try_load_file__missing_file__returns_none(self, tmp_path: Path) -> None:
        """Verify try_load_file returns None when target file is missing."""

        missing = tmp_path / "missing.bin"

        assert storage.try_load_file(missing) is None

    def test_try_load_file__directory_path__returns_none(self, tmp_path: Path) -> None:
        """Verify try_load_file returns None when path points to a directory."""

        directory = tmp_path / "subdir"
        directory.mkdir()

        assert storage.try_load_file(directory) is None

    def test_try_load_file__empty_path_string__returns_none(self) -> None:
        """Verify try_load_file returns None when path string is empty."""

        assert storage.try_load_file("") is None

    def test_try_load_file__null_byte_in_path__returns_none(self, tmp_path: Path) -> None:
        """Verify try_load_file returns None when path contains null bytes."""

        assert storage.try_load_file(str(tmp_path / "bad\x00.txt")) is None

    def test_try_load_file__unreadable_file__returns_none(self, tmp_path: Path) -> None:
        """Verify try_load_file returns None when file permissions prevent reading."""

        target = tmp_path / "unreadable.bin"
        target.write_bytes(b"restricted")
        os.chmod(target, 0)

        try:
            assert storage.try_load_file(target) is None
        finally:
            os.chmod(target, 0o600)


class TestEnsureFileExists:
    """Tests for ensure_file_exists."""

    def test_ensure_file_exists__valid_file_path__returns_resolved_path(self, tmp_path: Path) -> None:
        """Verify ensure_file_exists returns the resolved Path for a valid existing file."""

        target = tmp_path / "valid.txt"
        target.write_text("ok")

        resolved = storage.ensure_file_exists(target)

        assert resolved == target.resolve()

    def test_ensure_file_exists__valid_file_str__returns_resolved_path(self, tmp_path: Path) -> None:
        """Verify ensure_file_exists accepts string representations and returns Path."""

        target = tmp_path / "valid.txt"
        target.write_text("ok")

        resolved = storage.ensure_file_exists(str(target))

        assert resolved == target.resolve()

    def test_ensure_file_exists__valid_symlink_to_file__returns_resolved_target_path(self, tmp_path: Path) -> None:
        """Verify ensure_file_exists resolves symlinks to the canonical file target."""

        target = tmp_path / "actual.txt"
        target.write_text("canonical")
        link = tmp_path / "symlink.txt"
        link.symlink_to(target)

        resolved = storage.ensure_file_exists(link)

        assert resolved == target.resolve()

    def test_ensure_file_exists__empty_string_path__raises_storage_validation_error(self) -> None:
        """Verify ensure_file_exists rejects an empty path string."""

        with pytest.raises(config.StorageValidationError, match="File path cannot be empty"):
            storage.ensure_file_exists("")

    def test_ensure_file_exists__whitespace_only_path__raises_storage_validation_error(self) -> None:
        """Verify ensure_file_exists rejects whitespace-only paths."""

        with pytest.raises(config.StorageValidationError, match="File path cannot be empty"):
            storage.ensure_file_exists("   \t\n  ")

    def test_ensure_file_exists__null_byte_in_path__raises_storage_validation_error(self, tmp_path: Path) -> None:
        """Verify ensure_file_exists rejects paths containing null bytes."""

        bad_path = str(tmp_path / "corrupted\x00.txt")

        with pytest.raises(config.StorageValidationError, match="File path cannot contain null bytes") as exc_info:
            storage.ensure_file_exists(bad_path)

        assert exc_info.value.path == Path(bad_path)

    def test_ensure_file_exists__nonexistent_file__raises_storage_validation_error(self, tmp_path: Path) -> None:
        """Verify ensure_file_exists raises StorageValidationError on nonexistent file."""

        missing = tmp_path / "missing.txt"

        with pytest.raises(config.StorageValidationError, match="does not exist") as exc_info:
            storage.ensure_file_exists(missing)

        assert exc_info.value.path == missing.resolve()

    def test_ensure_file_exists__directory_target__raises_storage_validation_error(self, tmp_path: Path) -> None:
        """Verify ensure_file_exists raises StorageValidationError when path is a directory."""

        directory = tmp_path / "subdir"
        directory.mkdir()

        with pytest.raises(config.StorageValidationError, match="is not a file") as exc_info:
            storage.ensure_file_exists(directory)

        assert exc_info.value.path == directory.resolve()


class TestEnsureDirectoryExists:
    """Tests for ensure_directory_exists."""

    def test_ensure_directory_exists__valid_directory_path__returns_resolved_path(self, tmp_path: Path) -> None:
        """Verify ensure_directory_exists returns the resolved Path for an existing directory."""

        directory = tmp_path / "valid_dir"
        directory.mkdir()

        resolved = storage.ensure_directory_exists(directory)

        assert resolved == directory.resolve()

    def test_ensure_directory_exists__valid_directory_str__returns_resolved_path(self, tmp_path: Path) -> None:
        """Verify ensure_directory_exists accepts string representations of directories."""

        directory = tmp_path / "valid_dir"
        directory.mkdir()

        resolved = storage.ensure_directory_exists(str(directory))

        assert resolved == directory.resolve()

    def test_ensure_directory_exists__valid_symlink_to_directory__returns_resolved_target_path(self, tmp_path: Path) -> None:
        """Verify ensure_directory_exists resolves symlinks pointing to directories."""

        directory = tmp_path / "canonical_dir"
        directory.mkdir()
        link = tmp_path / "link_dir"
        link.symlink_to(directory)

        resolved = storage.ensure_directory_exists(link)

        assert resolved == directory.resolve()

    def test_ensure_directory_exists__empty_string_path__raises_storage_validation_error(self) -> None:
        """Verify ensure_directory_exists rejects an empty directory path string."""

        with pytest.raises(config.StorageValidationError, match="Directory path cannot be empty"):
            storage.ensure_directory_exists("")

    def test_ensure_directory_exists__whitespace_only_path__raises_storage_validation_error(self) -> None:
        """Verify ensure_directory_exists rejects whitespace-only directory paths."""

        with pytest.raises(config.StorageValidationError, match="Directory path cannot be empty"):
            storage.ensure_directory_exists("   \t\n  ")

    def test_ensure_directory_exists__null_byte_in_path__raises_storage_validation_error(self, tmp_path: Path) -> None:
        """Verify ensure_directory_exists rejects paths containing null bytes."""

        bad_path = str(tmp_path / "corrupted_dir\x00")

        with pytest.raises(config.StorageValidationError, match="Directory path cannot contain null bytes") as exc_info:
            storage.ensure_directory_exists(bad_path)

        assert exc_info.value.path == Path(bad_path)

    def test_ensure_directory_exists__nonexistent_directory__raises_storage_validation_error(self, tmp_path: Path) -> None:
        """Verify ensure_directory_exists raises StorageValidationError on missing directory."""

        missing = tmp_path / "missing_dir"

        with pytest.raises(config.StorageValidationError, match="does not exist") as exc_info:
            storage.ensure_directory_exists(missing)

        assert exc_info.value.path == missing.resolve()

    def test_ensure_directory_exists__file_target__raises_storage_validation_error(self, tmp_path: Path) -> None:
        """Verify ensure_directory_exists raises StorageValidationError when path is a regular file."""

        target = tmp_path / "file.txt"
        target.write_text("regular file")

        with pytest.raises(config.StorageValidationError, match="is not a directory") as exc_info:
            storage.ensure_directory_exists(target)

        assert exc_info.value.path == target.resolve()
