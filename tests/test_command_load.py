"""Tests for ``declusor.command.load.LoadPayload``.

Covers initialization (path validation), the ``execute`` path (raw-bytes write),
error handling when the file becomes unreadable, and edge cases.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_session() -> MagicMock:
    """Return a ``MagicMock`` satisfying the ``IConnection`` interface."""


@pytest.fixture
def mock_console() -> MagicMock:
    """Return a ``MagicMock`` satisfying the ``IConsole`` interface."""


@pytest.fixture
def temp_payload(tmp_path: Path) -> Path:
    """Create a temporary payload script with known content."""


# =============================================================================
# Tests: LoadPayload.__init__
# =============================================================================


def test_init_validates_file_exists(temp_payload: Path) -> None:
    """``ensure_file_exists`` must be invoked during construction."""


def test_init_accepts_string_path(temp_payload: Path) -> None:
    """A plain ``str`` path must be coerced to ``Path`` and validated."""


def test_init_accepts_path_object(temp_payload: Path) -> None:
    """A ``pathlib.Path`` object must be stored without conversion errors."""


def test_init_raises_on_nonexistent_file() -> None:
    """Constructing with a nonexistent path must raise ``InvalidOperation``."""


def test_init_stores_resolved_filepath(temp_payload: Path) -> None:
    """``_filepath`` must hold the resolved (absolute) ``Path``."""


# =============================================================================
# Tests: LoadPayload.execute
# =============================================================================


def test_execute_writes_raw_file_content(mock_session: MagicMock, mock_console: MagicMock, temp_payload: Path) -> None:
    """``session.write`` must receive the file's raw bytes (no base64 encoding)."""


def test_execute_writes_bytes_not_str(mock_session: MagicMock, mock_console: MagicMock, temp_payload: Path) -> None:
    """The value passed to ``session.write`` must be ``bytes``, not ``str``."""


def test_execute_reads_file_at_call_time(mock_session: MagicMock, mock_console: MagicMock, temp_payload: Path) -> None:
    """File content must be read during ``execute``, not cached at init time."""


def test_execute_raises_when_file_unreadable(mock_session: MagicMock, mock_console: MagicMock, temp_payload: Path) -> None:
    """If ``try_load_file`` returns ``None``, ``InvalidOperation`` must be raised."""


def test_execute_error_message_includes_filepath(mock_session: MagicMock, mock_console: MagicMock, temp_payload: Path) -> None:
    """The ``InvalidOperation`` message must contain the file path."""


# =============================================================================
# Tests: LoadPayload vs ExecuteFile
# =============================================================================


def test_sends_raw_content_not_base64() -> None:
    """Unlike ``ExecuteFile``, ``LoadPayload`` sends unencoded bytes."""


def test_does_not_have_opcode_attribute() -> None:
    """``LoadPayload`` must not define ``_OPCODE`` (unlike ``_BaseFileCommand`` subclasses)."""


# =============================================================================
# Tests: Edge cases
# =============================================================================


def test_handles_empty_file(mock_session: MagicMock, mock_console: MagicMock, tmp_path: Path) -> None:
    """A zero-byte payload file must result in ``session.write(b"")``."""


def test_handles_binary_content(mock_session: MagicMock, mock_console: MagicMock, tmp_path: Path) -> None:
    """Non-UTF-8 binary payload must be written verbatim."""


def test_handles_multiline_script(mock_session: MagicMock, mock_console: MagicMock, temp_payload: Path) -> None:
    """A multi-line script must preserve all newlines in the transmitted bytes."""
