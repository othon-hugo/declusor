"""Tests for ``declusor.util.network``.

Covers ``await_connection`` (the context-manager socket listener) and the
internal ``_handle_socket_exception`` helper (exception → ``ConnectionFailure``
mapping).
"""

import socket

import pytest

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def available_port() -> int:
    """Return an ephemeral port number that is currently available."""


@pytest.fixture
def mock_socket(monkeypatch: pytest.MonkeyPatch):
    """Replace ``socket.socket`` with a ``MagicMock``."""


# =============================================================================
# Tests: await_connection — success
# =============================================================================


def test_yields_connected_socket(available_port: int) -> None:
    """A successful handshake must yield a connected ``socket.socket``."""


def test_sets_reuse_addr(mock_socket) -> None:
    """``SO_REUSEADDR`` must be enabled for quick port reuse."""


def test_listens_on_port(mock_socket) -> None:
    """``bind`` and ``listen(1)`` must be called with the given host/port."""


def test_cleans_up_on_exit(available_port: int) -> None:
    """Both the listener and the client socket must be closed on context-manager exit."""


# =============================================================================
# Tests: await_connection — errors
# =============================================================================


def test_invalid_host_raises_connection_failure() -> None:
    """An unresolvable hostname must raise ``ConnectionFailure``."""


def test_port_out_of_range_raises_connection_failure() -> None:
    """A port > 65535 must raise ``ConnectionFailure``."""


def test_negative_port_raises_connection_failure() -> None:
    """A negative port must raise ``ConnectionFailure``."""


def test_permission_denied_raises_connection_failure() -> None:
    """Binding to a privileged port without root must raise ``ConnectionFailure``."""


def test_port_in_use_raises() -> None:
    """A port already bound by another process must raise an appropriate error."""


# =============================================================================
# Tests: _handle_socket_exception
# =============================================================================


def test_handles_gaierror() -> None:
    """``socket.gaierror`` must be mapped to ``ConnectionFailure`` with ``"invalid address/hostname"``."""


def test_handles_overflow_error() -> None:
    """``OverflowError`` must produce ``"port must be 0-65535"``."""


def test_handles_permission_error() -> None:
    """``PermissionError`` must produce ``"permission denied"``."""


def test_reraises_unknown_exception() -> None:
    """An unhandled exception type must be re-raised unchanged."""


def test_preserves_exception_chain() -> None:
    """Re-raised exceptions must carry the ``from`` clause."""


# =============================================================================
# Tests: await_connection — edge cases
# =============================================================================


def test_localhost_binding() -> None:
    """``host="127.0.0.1"`` must succeed."""


def test_all_interfaces_binding() -> None:
    """``host="0.0.0.0"`` must bind to all interfaces."""


def test_ipv4_only() -> None:
    """``AF_INET`` means only IPv4 addresses are supported."""


def test_single_connection_only() -> None:
    """``listen(1)`` means only one connection is accepted per invocation."""
