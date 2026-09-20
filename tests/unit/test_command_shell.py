"""Tests for ``declusor.command.shell.LaunchShell``.

Covers initialization (stop event creation), task management (request/response
handler threads), ``KeyboardInterrupt`` handling, and cooperative cancellation
via ``TaskPool``.
"""

from unittest.mock import MagicMock

import pytest

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_session() -> MagicMock:
    """Return a ``MagicMock`` satisfying the ``IConnection`` interface with ``read``/``write``."""


@pytest.fixture
def mock_console() -> MagicMock:
    """Return a ``MagicMock`` satisfying the ``IConsole`` interface."""


@pytest.fixture
def launch_shell():
    """Return a fresh ``LaunchShell`` instance."""


# =============================================================================
# Tests: LaunchShell.__init__
# =============================================================================


def test_init_creates_unset_stop_event() -> None:
    """``_stop_event`` must be a ``TaskEvent`` that is initially *not* set."""


# =============================================================================
# Tests: LaunchShell.execute — task management
# =============================================================================


def test_execute_registers_response_handler_as_background_task(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """A response-reading ``TaskHandler`` must be added to the ``TaskPool``."""


def test_execute_stops_task_pool_on_exit(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """``TaskPool.stop()`` must be called when ``execute`` returns, regardless of how."""


def test_execute_sets_stop_event_on_exit(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """The shared ``_stop_event`` must be set so background threads can exit."""


# =============================================================================
# Tests: LaunchShell.execute — exception handling
# =============================================================================


def test_execute_catches_keyboard_interrupt(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """A ``KeyboardInterrupt`` during execution must be caught, not propagated."""


def test_execute_does_not_propagate_keyboard_interrupt() -> None:
    """After catching ``KeyboardInterrupt``, ``execute`` must return normally."""


# =============================================================================
# Tests: _create_request_handler
# =============================================================================


def test_request_handler_writes_nonempty_input_to_session(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """Non-empty lines from ``console.read_line`` must be written to ``session``."""


def test_request_handler_skips_empty_input(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """Empty or whitespace-only input must *not* result in a ``session.write`` call."""


def test_request_handler_exits_on_stop_event(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """The handler loop must break once ``stop_event.is_set()`` returns ``True``."""


# =============================================================================
# Tests: _create_response_handler
# =============================================================================


def test_response_handler_streams_output_to_console(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """Bytes yielded by ``session.read`` must be forwarded via ``console.write_binary_data``."""


def test_response_handler_skips_empty_chunks(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """Empty ``bytes`` chunks from ``session.read`` must be silently dropped."""


def test_response_handler_removes_timeout_for_blocking_reads(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """``session.timeout`` must be set to ``None`` for the duration of the shell."""


def test_response_handler_restores_timeout_on_exit(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """The original ``session.timeout`` must be restored when the handler exits."""
