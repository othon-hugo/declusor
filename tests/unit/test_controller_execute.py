"""Tests for ``declusor.controller.execute.call_execute``.

Covers argument parsing, file validation, ``ExecuteFile`` creation, and
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
def temp_script(tmp_path: Path) -> Path:
    """Create a temporary script file for testing."""


# =============================================================================
# Tests: Argument parsing
# =============================================================================


def test_parses_filepath_argument(mock_session: MagicMock, mock_console: MagicMock, temp_script: Path) -> None:
    """``line=str(path)`` must be parsed as ``arguments["filepath"]``."""


def test_empty_line_raises_parser_error(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """An empty ``line`` must raise ``ParserError`` because ``filepath`` is required."""


# =============================================================================
# Tests: File validation
# =============================================================================


def test_validates_file_exists(mock_session: MagicMock, mock_console: MagicMock, temp_script: Path) -> None:
    """``ensure_file_exists`` must be called with the parsed filepath."""


def test_nonexistent_file_raises_invalid_operation(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """A path that does not exist must raise ``InvalidOperation``."""


def test_directory_path_raises_invalid_operation(mock_session: MagicMock, mock_console: MagicMock, tmp_path: Path) -> None:
    """A path pointing to a directory must raise ``InvalidOperation``."""


# =============================================================================
# Tests: Execution
# =============================================================================


def test_creates_execute_file_command(mock_session: MagicMock, mock_console: MagicMock, temp_script: Path) -> None:
    """``call_execute`` must instantiate ``ExecuteFile`` with the validated path."""


def test_writes_base64_command_to_session(mock_session: MagicMock, mock_console: MagicMock, temp_script: Path) -> None:
    """``session.write`` must be called with a base64-encoded command string."""


# =============================================================================
# Tests: Response handling
# =============================================================================


def test_reads_response_from_session(mock_session: MagicMock, mock_console: MagicMock, temp_script: Path) -> None:
    """``session.read()`` must be iterated after the command is sent."""


def test_writes_response_to_console(mock_session: MagicMock, mock_console: MagicMock, temp_script: Path) -> None:
    """Response chunks must be forwarded to ``console.write_binary_data``."""
