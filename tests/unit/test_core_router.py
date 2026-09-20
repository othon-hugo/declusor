"""Tests for ``declusor.core.router.Router``.

Covers initialization, the ``routes`` property, ``connect`` (registration),
``locate`` (lookup), ``get_route_usage`` (docstring extraction), and
``documentation`` (help-text generation).
"""

from unittest.mock import MagicMock

import pytest

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def router():
    """Return a fresh ``Router`` instance."""


@pytest.fixture
def sample_controller() -> MagicMock:
    """Return a mock controller callable with a docstring."""


# =============================================================================
# Tests: Router initialization
# =============================================================================


def test_init_creates_empty_route_table() -> None:
    """A new ``Router`` must have an empty ``route_table``."""


# =============================================================================
# Tests: Router.routes property
# =============================================================================


def test_routes_returns_tuple() -> None:
    """``routes`` must return a ``tuple`` of registered route names."""


def test_routes_empty_router_returns_empty_tuple() -> None:
    """An empty router must return ``()``."""


def test_routes_preserves_insertion_order() -> None:
    """Routes must appear in the order they were registered."""


# =============================================================================
# Tests: Router.connect
# =============================================================================


def test_connect_registers_route(sample_controller: MagicMock) -> None:
    """``connect("load", ctrl)`` must add ``"load"`` to the route table."""


def test_connect_strips_route_name(sample_controller: MagicMock) -> None:
    """Leading/trailing whitespace in the route name must be stripped."""


def test_connect_duplicate_raises_value_error(sample_controller: MagicMock) -> None:
    """Registering the same route twice must raise ``ValueError``."""


def test_connect_multiple_routes(sample_controller: MagicMock) -> None:
    """Multiple distinct routes must all be registered successfully."""


# =============================================================================
# Tests: Router.locate
# =============================================================================


def test_locate_returns_registered_controller(sample_controller: MagicMock) -> None:
    """``locate("shell")`` must return the controller registered under ``"shell"``."""


def test_locate_strips_route_name(sample_controller: MagicMock) -> None:
    """``locate(" shell ")`` must find the ``"shell"`` controller."""


def test_locate_unknown_raises_router_error() -> None:
    """``locate("unknown")`` must raise ``RouterError``."""


# =============================================================================
# Tests: Router.get_route_usage
# =============================================================================


def test_get_route_usage_returns_docstring(sample_controller: MagicMock) -> None:
    """The controller's docstring must be returned."""


def test_get_route_usage_joins_multiline_docstring(sample_controller: MagicMock) -> None:
    """A multi-line docstring must be joined into a single line."""


def test_get_route_usage_no_docstring_returns_empty() -> None:
    """A controller with ``__doc__ = None`` must produce an empty string."""


def test_get_route_usage_unknown_route_raises_router_error() -> None:
    """An unregistered route must raise ``RouterError``."""


# =============================================================================
# Tests: Router.documentation property
# =============================================================================


def test_documentation_lists_all_routes(sample_controller: MagicMock) -> None:
    """All registered route names must appear in the output."""


def test_documentation_aligns_columns() -> None:
    """Route names of different lengths must be left-padded for alignment."""


def test_documentation_includes_descriptions(sample_controller: MagicMock) -> None:
    """Each route line must include its controller's description."""


def test_documentation_empty_router() -> None:
    """An empty router must produce an empty/blank documentation string."""


def test_documentation_strips_trailing_newline() -> None:
    """The documentation string must not end with a trailing newline."""
