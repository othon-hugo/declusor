"""Tests for ``declusor.controller.upload.call_upload``.

Covers argument parsing, file validation, ``UploadFile`` command creation, and
response handling via ``_execute_and_read``.
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
def temp_file(tmp_path: Path) -> Path:
    """Create a temporary file for upload testing."""


# =============================================================================
# Tests: Argument parsing
# =============================================================================


def test_parses_filepath_argument(mock_session: MagicMock, mock_console: MagicMock, temp_file: Path) -> None:
    """``line=str(path)`` must be parsed as ``arguments["filepath"]``."""


def test_empty_line_raises_parser_error(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """An empty ``line`` must raise ``ParserError`` because ``filepath`` is required."""


def test_parses_quoted_path_with_spaces(mock_session: MagicMock, mock_console: MagicMock, temp_file: Path) -> None:
    """A path containing spaces enclosed in quotes must be parsed correctly."""


# =============================================================================
# Tests: File validation
# =============================================================================


def test_validates_file_exists(mock_session: MagicMock, mock_console: MagicMock, temp_file: Path) -> None:
    """``ensure_file_exists`` must be called with the parsed filepath."""


def test_nonexistent_file_raises_invalid_operation(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """A path that does not exist must raise ``InvalidOperation``."""


def test_directory_path_raises_invalid_operation(mock_session: MagicMock, mock_console: MagicMock, tmp_path: Path) -> None:
    """A directory path must raise ``InvalidOperation``."""


# =============================================================================
# Tests: Execution
# =============================================================================


def test_creates_upload_file_command(mock_session: MagicMock, mock_console: MagicMock, temp_file: Path) -> None:
    """``call_upload`` must instantiate ``UploadFile`` with the validated path."""


def test_writes_base64_store_command_to_session(mock_session: MagicMock, mock_console: MagicMock, temp_file: Path) -> None:
    """``session.write`` must receive a base64-encoded store command."""


# =============================================================================
# Tests: Response handling
# =============================================================================


def test_reads_response_from_session(mock_session: MagicMock, mock_console: MagicMock, temp_file: Path) -> None:
    """``session.read()`` must be iterated after uploading."""


def test_writes_response_to_console(mock_session: MagicMock, mock_console: MagicMock, temp_file: Path) -> None:
    """Upload confirmation chunks must be forwarded to ``console.write_binary_data``."""


def test_shows_stored_path_in_response(mock_session: MagicMock, mock_console: MagicMock, temp_file: Path) -> None:
    """If the server returns a stored path, it must appear in the console output."""
