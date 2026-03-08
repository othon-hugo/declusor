"""Tests for ``declusor.controller.shell.call_shell``.

Covers argument parsing (no arguments accepted), ``LaunchShell`` creation,
execution delegation, and verification that the controller does not directly
handle session I/O.
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


def test_accepts_empty_line(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """``line=""`` must be accepted without error (``shell`` takes no arguments)."""


def test_rejects_extra_arguments(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """``line="unexpected args"`` must raise ``ParserError``."""


def test_uses_empty_argument_definitions(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """``parse_command_arguments`` must be called with an empty definition dict ``{}``."""


# =============================================================================
# Tests: Execution
# =============================================================================


def test_creates_launch_shell_instance(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """``call_shell`` must instantiate ``LaunchShell()``."""


def test_calls_execute_on_session(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """``LaunchShell.execute(session, console)`` must be called."""


# =============================================================================
# Tests: I/O delegation
# =============================================================================


def test_does_not_read_session_directly(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """``session.read()`` must *not* be called by the controller (``LaunchShell`` owns I/O)."""


def test_does_not_write_to_console_directly(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """``console.write_*`` must *not* be called by the controller."""
