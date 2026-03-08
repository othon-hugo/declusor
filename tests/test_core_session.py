"""Tests for ``declusor.connection.shell_socket.ShellSocketConnection``.

Covers initialization (socket storage, timeout/bufsize defaults), the
``initialize`` handshake (ACK validation, error paths), ``set_timeout``,
the ``read`` generator (ACK framing, split ACK, timeout, connection close),
and the ``write`` method (content + ACK, error handling).
"""

from unittest.mock import MagicMock

import pytest

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_socket() -> MagicMock:
    """Return a ``MagicMock`` mimicking a ``socket.socket``."""


@pytest.fixture
def connection(mock_socket: MagicMock):
    """Return a ``ShellSocketConnection`` instance with a mocked socket."""


# =============================================================================
# Tests: Initialization
# =============================================================================


def test_init_stores_socket(mock_socket: MagicMock) -> None:
    """``_socket`` must reference the provided socket."""


def test_init_default_timeout() -> None:
    """The default ``_timeout`` must be ``0.75`` seconds."""


def test_init_default_bufsize() -> None:
    """The default ``_bufsize`` must be ``4096`` bytes."""


def test_init_custom_timeout(mock_socket: MagicMock) -> None:
    """A custom ``timeout`` keyword must override the default."""


def test_init_custom_bufsize(mock_socket: MagicMock) -> None:
    """A custom ``bufsize`` keyword must override the default."""


# =============================================================================
# Tests: initialize (library-upload handshake)
# =============================================================================


def test_initialize_writes_library_content(mock_socket: MagicMock) -> None:
    """The shell library bytes must be sent via ``write``."""


def test_initialize_validates_client_ack(mock_socket: MagicMock) -> None:
    """A proper ACK response must be accepted silently."""


def test_initialize_raises_on_bad_ack(mock_socket: MagicMock) -> None:
    """An unexpected response must raise ``ConnectionFailure``."""


def test_initialize_raises_on_timeout(mock_socket: MagicMock) -> None:
    """No response within the timeout must raise ``ConnectionFailure``."""


def test_initialize_raises_on_os_error(mock_socket: MagicMock) -> None:
    """An ``OSError`` during ``recv`` must raise ``ConnectionFailure``."""


# =============================================================================
# Tests: set_timeout
# =============================================================================


def test_set_timeout_updates_value() -> None:
    """``set_timeout(5.0)`` must update ``_timeout`` to ``5.0``."""


# =============================================================================
# Tests: read (ACK-framed generator)
# =============================================================================


def test_read_yields_data_chunks(mock_socket: MagicMock) -> None:
    """Data preceding the ACK must be yielded as ``bytes`` chunks."""


def test_read_stops_at_ack(mock_socket: MagicMock) -> None:
    """Iteration must stop as soon as the client ACK is detected."""


def test_read_handles_split_ack(mock_socket: MagicMock) -> None:
    """An ACK split across two ``recv`` calls must be correctly detected."""


def test_read_raises_on_connection_closed(mock_socket: MagicMock) -> None:
    """``recv`` returning ``b""`` must raise ``ConnectionResetError``."""


def test_read_continues_on_timeout(mock_socket: MagicMock) -> None:
    """A ``socket.timeout`` must *not* break the read loop."""


def test_read_yields_partial_buffer(mock_socket: MagicMock) -> None:
    """Only safe portions before a possible split ACK must be yielded."""


# =============================================================================
# Tests: write
# =============================================================================


def test_write_sends_content(mock_socket: MagicMock) -> None:
    """``write(b"cmd")`` must call ``socket.send`` with the content."""


def test_write_appends_server_ack(mock_socket: MagicMock) -> None:
    """The server ACK value must be appended after the content."""


def test_write_sends_immediately(mock_socket: MagicMock) -> None:
    """``socket.send`` must be called in the same call frame."""


def test_write_raises_on_os_error(mock_socket: MagicMock) -> None:
    """An ``OSError`` during ``send`` must raise ``ConnectionFailure``."""


def test_write_preserves_exception_chain(mock_socket: MagicMock) -> None:
    """The original ``OSError`` must be chained with ``from``."""
