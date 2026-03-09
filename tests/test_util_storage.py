"""Tests for the ``declusor.util.storage`` module."""

from pathlib import Path

import pytest

from declusor import config
from declusor.util import storage


# =============================================================================
# Tests: storage.load_file (Reading file content)
# =============================================================================

def test_load_file_returns_file_content_as_bytes(temp_file: Path) -> None:
    """Loading an existing file must read and return its exact contents as bytes."""

    # ARRANGE: Use the pytest ``temp_file`` fixture containing known output

    # ACT: Process file load
    content = storage.load_file(temp_file)

    # ASSERT: Loaded content should safely match strictly as bytes
    assert content == b"file content for testing"

def test_load_file_raises_invalid_operation_if_unreadable(tmp_path: Path) -> None:
    """Loading a file that triggers an OS error must raise an ``InvalidOperation`` error."""

    # ARRANGE: Create valid dummy file and restrict all read access manually
    test_file = tmp_path / "protected.txt"
    test_file.touch()
    test_file.chmod(0o000)

    try:
        # ACT & ASSERT: Reading an unavailable resource propagates library-specific unified error code
        with pytest.raises(config.InvalidOperation, match="could not read file"):
            storage.load_file(test_file)
    finally:
        # Restore permissions allowing temporary cleanup success
        test_file.chmod(0o600)


# =============================================================================
# Tests: storage.try_load_file (Graceful file loading)
# =============================================================================

def test_try_load_file_returns_bytes_for_existing_file(temp_file: Path) -> None:
    """Trying to load a valid file must return its bytes content."""

    # ARRANGE: Existing test file populated in scope

    # ACT: Evaluate safe-loading method wrapper
    content = storage.try_load_file(temp_file)

    # ASSERT: The file's payload is fully processed correctly inside the exception-blocking utility
    assert content == b"file content for testing"

def test_try_load_file_returns_none_for_missing_file(tmp_path: Path) -> None:
    """Trying to load an invalid or missing file must silently return ``None``."""

    # ARRANGE: Uncreated fictional path targeting temp space
    fictional_file = tmp_path / "does_not_exist.raw"

    # ACT: Try reading the placeholder cleanly
    content = storage.try_load_file(fictional_file)

    # ASSERT: Operation skips exceptions returning explicit ``None`` values
    assert content is None


# =============================================================================
# Tests: storage.ensure_file_exists (File presence validation)
# =============================================================================

def test_ensure_file_exists_returns_resolved_path(temp_file: Path) -> None:
    """Ensuring a valid file exists must return its fully resolved path."""

    # ARRANGE: Provide current path variable initialized from temp_file scope

    # ACT: Resolve and guarantee element constraint presence
    result = storage.ensure_file_exists(temp_file)

    # ASSERT: Valid paths are safely echoed through after successful resolution
    assert result == temp_file.resolve()

def test_ensure_file_exists_raises_invalid_operation_if_missing(tmp_path: Path) -> None:
    """Ensuring a non-existent file exists must raise an ``InvalidOperation`` error."""

    # ARRANGE: Missing file
    missing = tmp_path / "missing.md"

    # ACT & ASSERT: Execution breaks indicating specific file is absent
    with pytest.raises(config.InvalidOperation, match="does not exist"):
        storage.ensure_file_exists(missing)

def test_ensure_file_exists_raises_invalid_operation_if_directory(tmp_path: Path) -> None:
    """Ensuring a path exists that points to a directory instead of a file must raise an ``InvalidOperation`` error."""

    # ARRANGE: Directory constructed as parameter instead of flat data structure
    dir_path = tmp_path

    # ACT & ASSERT: Checks should fail specifically indicating it's not a generic file
    with pytest.raises(config.InvalidOperation, match="is not a file"):
        storage.ensure_file_exists(dir_path)


# =============================================================================
# Tests: storage.ensure_directory_exists (Directory presence validation)
# =============================================================================

def test_ensure_directory_exists_returns_resolved_path(tmp_path: Path) -> None:
    """Ensuring a valid directory exists must return its fully resolved path."""

    # ARRANGE: Initialize default standard workspace
    test_dir = tmp_path / "folder"
    test_dir.mkdir()

    # ACT: Verify existence checks yield confirmed paths
    result = storage.ensure_directory_exists(test_dir)

    # ASSERT: Fully formed resolution paths provided
    assert result == test_dir.resolve()

def test_ensure_directory_exists_raises_invalid_operation_if_missing(tmp_path: Path) -> None:
    """Ensuring a non-existent directory exists must raise an ``InvalidOperation`` error."""

    # ARRANGE: Non-existent missing child folder
    missing_dir = tmp_path / "unstructured_dir"

    # ACT & ASSERT: Exception must explicitly clarify directory targets are absent
    with pytest.raises(config.InvalidOperation, match="does not exist"):
        storage.ensure_directory_exists(missing_dir)

def test_ensure_directory_exists_raises_invalid_operation_if_file(temp_file: Path) -> None:
    """Ensuring a path exists that points to a file instead of a directory must raise an ``InvalidOperation`` error."""

    # ARRANGE: Temp text fixture from global execution scope

    # ACT & ASSERT: Verification must prevent treating valid items incorrectly
    with pytest.raises(config.InvalidOperation, match="is not a directory"):
        storage.ensure_directory_exists(temp_file)
