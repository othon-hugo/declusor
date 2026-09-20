"""Tests for ``declusor.command.execute.ExecuteCommand``.

Verifies initialization encoding, execute-time transmission, and
edge-case handling (empty strings, unicode, special characters).
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
# Tests: ExecuteCommand.__init__
# =============================================================================


def test_init_encodes_command_as_utf8_bytes() -> None:
    """UTF-8 encode the command string and store it as ``_command_line``."""


def test_init_stores_empty_bytes_for_empty_string() -> None:
    """An empty command string should produce ``b""``."""


def test_init_encodes_unicode_characters() -> None:
    """Non-ASCII characters (e.g. CJK) must survive the UTF-8 round-trip."""


def test_init_preserves_shell_special_characters() -> None:
    """Shell metacharacters (``$``, ``&&``, ``|``) must not be altered."""


# =============================================================================
# Tests: ExecuteCommand.execute
# =============================================================================


def test_execute_writes_encoded_command_to_session(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """``session.write`` must be called once with the pre-encoded bytes."""


def test_execute_does_not_read_from_session(mock_session: MagicMock, mock_console: MagicMock) -> None:
    """``execute`` only writes; reading is the caller's responsibility."""
