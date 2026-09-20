"""Tests for ``declusor.util.storage``.

Covers ``load_file``, ``try_load_file``, ``ensure_file_exists``, and
``ensure_directory_exists``.
"""

from pathlib import Path

import pytest

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_file(tmp_path: Path) -> Path:
    """Create a temporary file with known content."""


@pytest.fixture
def temp_directory(tmp_path: Path) -> Path:
    """Create a temporary directory structure."""


# =============================================================================
# Tests: load_file
# =============================================================================


def test_load_file_returns_bytes(temp_file: Path) -> None:
    """The file's exact byte content must be returned."""


def test_load_file_accepts_string_path(temp_file: Path) -> None:
    """A ``str`` path must be accepted and coerced internally."""


def test_load_file_raises_on_nonexistent() -> None:
    """A nonexistent path must raise ``InvalidOperation``."""


def test_load_file_raises_on_directory(temp_directory: Path) -> None:
    """A directory path must raise ``InvalidOperation``."""


def test_load_file_raises_on_permission_denied(temp_file: Path) -> None:
    """An unreadable file must raise ``InvalidOperation``."""


def test_load_file_handles_binary_content(temp_file: Path) -> None:
    """Non-UTF-8 binary data must be returned without modification."""


def test_load_file_handles_empty_file(temp_file: Path) -> None:
    """A zero-byte file must return ``b""``."""


# =============================================================================
# Tests: try_load_file
# =============================================================================


def test_try_load_file_returns_content(temp_file: Path) -> None:
    """A readable file must return its byte content."""


def test_try_load_file_returns_none_on_missing() -> None:
    """A nonexistent path must return ``None``."""


def test_try_load_file_returns_none_on_permission_error(temp_file: Path) -> None:
    """An unreadable file must return ``None``."""


# =============================================================================
# Tests: ensure_file_exists
# =============================================================================


def test_ensure_file_returns_resolved_path(temp_file: Path) -> None:
    """The returned ``Path`` must be fully resolved (absolute)."""


def test_ensure_file_resolves_relative_path(temp_file: Path) -> None:
    """A relative path must be resolved to an absolute path."""


def test_ensure_file_raises_on_nonexistent() -> None:
    """A nonexistent path must raise ``InvalidOperation``."""


def test_ensure_file_raises_on_directory(temp_directory: Path) -> None:
    """A directory must raise ``InvalidOperation``."""


def test_ensure_file_accepts_string(temp_file: Path) -> None:
    """A ``str`` path must be accepted."""


# =============================================================================
# Tests: ensure_directory_exists
# =============================================================================


def test_ensure_dir_returns_resolved_path(temp_directory: Path) -> None:
    """The returned ``Path`` must be fully resolved (absolute)."""


def test_ensure_dir_resolves_relative_path(temp_directory: Path) -> None:
    """A relative path must be resolved to an absolute path."""


def test_ensure_dir_raises_on_nonexistent() -> None:
    """A nonexistent path must raise ``InvalidOperation``."""


def test_ensure_dir_raises_on_file(temp_file: Path) -> None:
    """A file path must raise ``InvalidOperation``."""


def test_ensure_dir_accepts_string(temp_directory: Path) -> None:
    """A ``str`` path must be accepted."""
