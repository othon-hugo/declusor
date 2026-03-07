"""Tests for ``declusor.controller.exit.call_exit``.

Verifies that ``call_exit`` raises ``ExitRequest``, ignores its arguments,
and does not interact with the session or console.
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
# Tests: call_exit
# =============================================================================


def test_raises_exit_request(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """``call_exit`` must raise ``ExitRequest`` unconditionally."""


def test_ignores_line_argument(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """Passing a non-empty ``line`` must still raise ``ExitRequest``."""


def test_does_not_call_session_methods(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """Neither ``session.read`` nor ``session.write`` must be called."""


def test_exit_request_is_declusor_exception() -> None:
    """``ExitRequest`` must be a subclass of ``DeclusorException``."""
