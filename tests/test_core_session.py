"""Tests for declusor.core.session module (Session class).

This module tests the synchronous session management including:
- Session: Manages socket connection for reading/writing data
- ACK-based protocol for message framing
- Timeout and buffer size configuration
"""

from unittest.mock import MagicMock

import pytest

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_socket() -> MagicMock:
    """Create a mock socket."""


@pytest.fixture
def session(mock_socket: MagicMock):
    """Create a Session instance with mocked socket."""


# =============================================================================
# Tests: Session initialization
# =============================================================================


def test_session_init_stores_socket(mock_socket: MagicMock) -> None:
    """
    Given: Session is created with socket
    When: __init__ is called
    Then: socket attribute is set
    """


def test_session_init_default_timeout() -> None:
    """
    Given: Session is created without timeout argument
    When: __init__ is called
    Then: _timeout is set to default 0.75 seconds
    """


def test_session_init_default_bufsize() -> None:
    """
    Given: Session is created without bufsize argument
    When: __init__ is called
    Then: _bufsize is set to default 4096 bytes
    """


def test_session_init_custom_timeout(mock_socket: MagicMock) -> None:
    """
    Given: Session is created with timeout=2.0
    When: __init__ is called
    Then: _timeout is set to 2.0
    """


def test_session_init_custom_bufsize(mock_socket: MagicMock) -> None:
    """
    Given: Session is created with bufsize=8192
    When: __init__ is called
    Then: _bufsize is set to 8192
    """


# =============================================================================
# Tests: Session.initialize
# =============================================================================


def test_session_initialize_loads_library(mock_socket: MagicMock) -> None:
    """
    Given: Session.initialize() is called
    When: Initialization runs
    Then: Writes library content via session.write()
    """


def test_session_initialize_checks_ack(mock_socket: MagicMock) -> None:
    """
    Given: Client sends proper ACK after library load
    When: initialize() reads response
    Then: No warning is displayed
    """


def test_session_initialize_raises_on_bad_ack(mock_socket: MagicMock) -> None:
    """
    Given: Client sends unexpected response (not ACK)
    When: initialize() reads response
    Then: Raises ConnectionError about invalid client ACK
    """


def test_session_initialize_raises_on_timeout(mock_socket: MagicMock) -> None:
    """
    Given: Client does not respond within timeout
    When: initialize() times out
    Then: Raises ConnectionError about timeout waiting for client ACK
    """


def test_session_initialize_raises_on_oserror(mock_socket: MagicMock) -> None:
    """
    Given: socket.recv() raises OSError during initialization
    When: initialize() attempts to read ACK
    Then: Raises ConnectionError with descriptive message
    """


# =============================================================================
# Tests: Session.set_timeout
# =============================================================================


def test_session_set_timeout_updates_value() -> None:
    """
    Given: Session with default timeout
    When: set_timeout(5.0) is called
    Then: _timeout is updated to 5.0
    """


# =============================================================================
# Tests: Session.read
# =============================================================================


def test_session_read_yields_data_chunks(mock_socket: MagicMock) -> None:
    """
    Given: Client sends data followed by ACK
    When: read() generator is iterated
    Then: Yields data chunks (excluding ACK)
    """


def test_session_read_stops_at_ack(mock_socket: MagicMock) -> None:
    """
    Given: Client sends "data" + ACK_CLIENT_VALUE
    When: read() is iterated
    Then: Yields "data" and stops (ACK marks end)
    """


def test_session_read_handles_split_ack(mock_socket: MagicMock) -> None:
    """
    Given: ACK is split across two read() calls
    When: read() processes chunks
    Then: Correctly detects ACK spanning buffer boundary
    """


def test_session_read_raises_on_connection_closed(mock_socket: MagicMock) -> None:
    """
    Given: socket.recv() returns empty bytes (connection closed)
    When: read() processes
    Then: Raises ConnectionResetError
    """


def test_session_read_continues_on_timeout(mock_socket: MagicMock) -> None:
    """
    Given: socket.recv() times out (socket.timeout)
    When: read() handles timeout
    Then: Continues reading (does not break loop)
    """


def test_session_read_yields_partial_buffer(mock_socket: MagicMock) -> None:
    """
    Given: Large data arriving in multiple chunks before ACK
    When: read() processes data
    Then: Yields safe portions while ACK might span chunks
    """


# =============================================================================
# Tests: Session.write
# =============================================================================


def test_session_write_sends_content(mock_socket: MagicMock) -> None:
    """
    Given: write(b"command") is called
    When: Data is sent
    Then: socket.send(b"command") is called
    """


def test_session_write_appends_server_ack(mock_socket: MagicMock) -> None:
    """
    Given: write(b"data") is called
    When: Data is sent
    Then: ACK_SERVER_VALUE is appended after content
    """


def test_session_write_sends_immediately(mock_socket: MagicMock) -> None:
    """
    Given: write() is called
    When: Data is sent
    Then: socket.send() is called immediately
    """


def test_session_write_raises_on_oserror(mock_socket: MagicMock) -> None:
    """
    Given: socket.send() raises OSError
    When: write() attempts to send
    Then: Raises ConnectionError with descriptive message
    """


def test_session_write_preserves_exception_chain(mock_socket: MagicMock) -> None:
    """
    Given: OSError is raised during write
    When: ConnectionError is raised
    Then: Original OSError is chained with 'from'
    """
