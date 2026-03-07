"""Tests for ``declusor.controller.load.call_load``.

Covers argument parsing, file validation, ``LoadPayload`` creation, and
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
def temp_payload(tmp_path: Path) -> Path:
    """Create a temporary payload file for testing."""


# =============================================================================
# Tests: Argument parsing
# =============================================================================


def test_parses_filepath_argument(mock_session: MagicMock, mock_console: MagicMock, temp_payload: Path) -> None:
    """``line=str(path)`` must be parsed as ``arguments["filepath"]``."""


def test_empty_line_raises_parser_error(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """An empty ``line`` must raise ``ParserError`` because ``filepath`` is required."""


def test_parses_relative_path(mock_session: MagicMock, mock_console: MagicMock, temp_payload: Path) -> None:
    """A relative path like ``"discovery/dev_tools.sh"`` must be parsed correctly."""


# =============================================================================
# Tests: File validation
# =============================================================================


def test_validates_file_exists(mock_session: MagicMock, mock_console: MagicMock, temp_payload: Path) -> None:
    """``ensure_file_exists`` must be called with the parsed filepath."""


def test_nonexistent_file_raises_invalid_operation(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """A path that does not exist must raise ``InvalidOperation``."""


# =============================================================================
# Tests: Execution
# =============================================================================


def test_creates_load_payload_command(mock_session: MagicMock, mock_console: MagicMock, temp_payload: Path) -> None:
    """``call_load`` must instantiate ``LoadPayload`` with the validated path."""


def test_writes_raw_content_to_session(mock_session: MagicMock, mock_console: MagicMock, temp_payload: Path) -> None:
    """``session.write`` must receive the raw script bytes (no base64)."""


# =============================================================================
# Tests: Response handling
# =============================================================================


def test_reads_response_from_session(mock_session: MagicMock, mock_console: MagicMock, temp_payload: Path) -> None:
    """``session.read()`` must be iterated after sending the payload."""


def test_writes_response_to_console(mock_session: MagicMock, mock_console: MagicMock, temp_payload: Path) -> None:
    """Response chunks must be forwarded to ``console.write_binary_data``."""


def test_handles_multiline_output(mock_session: MagicMock, mock_console: MagicMock, temp_payload: Path) -> None:
    """All chunks from a multi-part response must be written to console."""
