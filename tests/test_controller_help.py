"""Tests for ``declusor.controller.help.create_help_controller``.

Covers the factory function, global help (no argument), per-command help,
argument parsing, and closure behaviour with injected providers.
"""

from typing import Callable
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
def mock_get_documentation() -> Callable[[], str]:
    """Return a mock callable that produces a full help string."""


@pytest.fixture
def mock_get_route_usage() -> Callable[[str], str]:
    """Return a mock callable that produces per-route usage text."""


# =============================================================================
# Tests: Factory function
# =============================================================================


def test_returns_callable(mock_get_documentation: Callable, mock_get_route_usage: Callable) -> None:
    """``create_help_controller`` must return a callable controller function."""


# =============================================================================
# Tests: Global help (empty line)
# =============================================================================


def test_empty_line_displays_all_commands(
    mock_session: MagicMock, mock_console: MagicMock,
    mock_get_documentation: Callable, mock_get_route_usage: Callable,
) -> None:
    """With ``line=""``, the full documentation string must be printed."""


def test_empty_line_writes_to_console(
    mock_session: MagicMock, mock_console: MagicMock,
    mock_get_documentation: Callable, mock_get_route_usage: Callable,
) -> None:
    """``console.write_message`` must receive the ``get_documentation()`` result."""


# =============================================================================
# Tests: Per-command help
# =============================================================================


def test_command_arg_displays_specific_help(
    mock_session: MagicMock, mock_console: MagicMock,
    mock_get_documentation: Callable, mock_get_route_usage: Callable,
) -> None:
    """``line="load"`` must display just the ``load`` route's usage."""


def test_command_arg_calls_get_route_usage(
    mock_session: MagicMock, mock_console: MagicMock,
    mock_get_documentation: Callable, mock_get_route_usage: Callable,
) -> None:
    """``get_route_usage`` must be called with the provided route name."""


def test_command_arg_writes_usage_to_console(
    mock_session: MagicMock, mock_console: MagicMock,
    mock_get_documentation: Callable, mock_get_route_usage: Callable,
) -> None:
    """``console.write_message`` must receive the per-route usage string."""


# =============================================================================
# Tests: Argument parsing
# =============================================================================


def test_optional_command_defaults_to_none(
    mock_session: MagicMock, mock_console: MagicMock,
    mock_get_documentation: Callable, mock_get_route_usage: Callable,
) -> None:
    """When no argument is given, ``command`` must be ``None`` (uses global help)."""


def test_provided_command_arg_parsed_correctly(
    mock_session: MagicMock, mock_console: MagicMock,
    mock_get_documentation: Callable, mock_get_route_usage: Callable,
) -> None:
    """``line="upload"`` must parse ``command`` as ``"upload"``."""


# =============================================================================
# Tests: Closure behaviour
# =============================================================================


def test_uses_injected_documentation_provider(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """The controller returned by the factory must call the injected ``get_documentation``."""


def test_uses_injected_route_usage_provider(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """The controller returned by the factory must call the injected ``get_route_usage``."""
