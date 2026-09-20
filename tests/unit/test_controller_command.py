"""Tests for ``declusor.controller.command.call_command``.

Covers argument parsing, ``ExecuteCommand`` creation and execution, and the
``_execute_and_read`` helper (response reading and console output).
"""

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


# =============================================================================
# Tests: Argument parsing
# =============================================================================


def test_parses_unquoted_command_argument(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """``line="ls -la"`` must be parsed as ``arguments["command"] == "ls -la"``."""


def test_parses_quoted_command_argument(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """A quoted argument like ``'"echo hello"'`` must preserve inner spaces."""


def test_empty_line_raises_parser_error(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """An empty ``line`` must raise ``ParserError`` because ``command`` is required."""


# =============================================================================
# Tests: Execution
# =============================================================================


def test_creates_execute_command_instance(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """``call_command`` must instantiate ``ExecuteCommand`` with the parsed command."""


def test_writes_encoded_command_to_session(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """``session.write`` must be called with the UTF-8 encoded command bytes."""


# =============================================================================
# Tests: Response handling (via _execute_and_read)
# =============================================================================


def test_reads_response_from_session(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """``session.read()`` must be iterated after writing the command."""


def test_writes_response_chunks_to_console(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """Each non-empty chunk yielded by ``session.read()`` must be forwarded to ``console.write_binary_data``."""


def test_handles_empty_response(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """If ``session.read()`` yields nothing, no output must be written to console."""


def test_handles_multipart_response(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """Multiple chunks from ``session.read()`` must each be written to console."""
