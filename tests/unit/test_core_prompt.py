"""Tests for ``declusor.core.prompt.PromptCLI``.

Covers initialization, ``read_command`` (looping until non-empty input),
``handle_route`` (command lookup and dispatch), and the ``run`` loop
(exit conditions and exception handling).
"""

from unittest.mock import MagicMock

import pytest

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_router() -> MagicMock:
    """Return a ``MagicMock`` satisfying the ``IRouter`` interface."""


@pytest.fixture
def mock_session() -> MagicMock:
    """Return a ``MagicMock`` satisfying the ``IConnection`` interface."""


@pytest.fixture
def mock_console() -> MagicMock:
    """Return a ``MagicMock`` satisfying the ``IConsole`` interface."""


@pytest.fixture
def prompt_cli(mock_router: MagicMock, mock_session: MagicMock, mock_console: MagicMock):
    """Return a ``PromptCLI`` instance with mocked dependencies."""


# =============================================================================
# Tests: PromptCLI initialization
# =============================================================================


def test_init_sets_prompt_format() -> None:
    """``_prompt`` must follow the pattern ``"[<name>] "``."""


def test_init_stores_router() -> None:
    """``_router`` must reference the injected router."""


def test_init_stores_session() -> None:
    """``_session`` must reference the injected session."""


def test_init_stores_console() -> None:
    """``_console`` must reference the injected console."""


# =============================================================================
# Tests: PromptCLI.read_command
# =============================================================================


def test_read_command_returns_non_empty_input(mock_console: MagicMock) -> None:
    """The first non-empty stripped input must be returned."""


def test_read_command_skips_empty_lines(mock_console: MagicMock) -> None:
    """Empty or whitespace-only lines must be skipped until a real command arrives."""


def test_read_command_displays_prompt(mock_console: MagicMock) -> None:
    """``console.read_stripped_line`` must be called with the ``_prompt`` string."""


# =============================================================================
# Tests: PromptCLI.handle_route — command dispatch
# =============================================================================


def test_handle_route_parses_command_and_argument(mock_router: MagicMock) -> None:
    """``"load myfile.sh"`` must dispatch to the ``"load"`` controller with ``"myfile.sh"``."""


def test_handle_route_empty_argument_when_no_space(mock_router: MagicMock) -> None:
    """``"exit"`` must dispatch to the ``"exit"`` controller with ``""``."""


def test_handle_route_strips_argument_whitespace(mock_router: MagicMock) -> None:
    """Trailing spaces in the argument must be stripped."""


def test_handle_route_passes_session_and_console(mock_router: MagicMock) -> None:
    """The controller must receive ``(session, console, argument)``."""


# =============================================================================
# Tests: PromptCLI.handle_route — error handling
# =============================================================================


def test_handle_route_unknown_command_raises_router_error(mock_router: MagicMock) -> None:
    """An unregistered command must raise ``RouterError``."""


# =============================================================================
# Tests: PromptCLI.run — main loop
# =============================================================================


def test_run_loops_until_exit() -> None:
    """Multiple commands must be processed sequentially until exit."""


def test_run_exits_on_exit_request() -> None:
    """``ExitRequest`` raised by a controller must break the loop."""


def test_run_exits_on_keyboard_interrupt_at_prompt() -> None:
    """``KeyboardInterrupt`` during ``read_command`` must break the loop."""


def test_run_catches_declusor_exception(mock_console: MagicMock) -> None:
    """A ``DeclusorException`` from a controller must be caught and printed, not propagated."""


def test_run_displays_error_message_on_declusor_exception(mock_console: MagicMock) -> None:
    """``console.write_error_message`` must be called with the exception."""


def test_run_continues_on_keyboard_interrupt_in_command() -> None:
    """``KeyboardInterrupt`` during ``handle_route`` must *not* exit the loop."""


def test_read_command_propagates_keyboard_interrupt() -> None:
    """``KeyboardInterrupt`` during input must be re-raised to the caller."""
