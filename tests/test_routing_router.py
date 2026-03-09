"""Tests for the ``declusor.routing.router`` module."""

import pytest

from declusor import config
from declusor.interface import connection, console
from declusor.routing import router


# =============================================================================
# Dummies/Mocks
# =============================================================================

def dummy_controller_with_doc(conn: connection.IConnection, term: console.IConsole, arg: str) -> None:
    """A dummy controller with a
    multi-line docstring."""

def dummy_controller_no_doc(conn: connection.IConnection, term: console.IConsole, arg: str) -> None:
    # A dummy controller without a docstring to test edge cases where the router
    # checks the `__doc__` format and needs to handle `None`.
    pass


# =============================================================================
# Tests: Router.connect (Route registration)
# =============================================================================

def test_router_connect_registers_new_route() -> None:
    """Connecting a new route must register the controller in the internal table."""

    # ARRANGE: Create a new router instance
    r = router.Router()

    # ACT: Connect a valid route name to a dummy controller
    r.connect("cmd", dummy_controller_no_doc)

    # ASSERT: The route should be present in the routes tuple
    assert "cmd" in r.routes
    assert r.locate("cmd") is dummy_controller_no_doc

def test_router_connect_strips_route_name() -> None:
    """Connecting a route with surrounding whitespace must register it stripped."""

    # ARRANGE: Create a new router instance
    r = router.Router()

    # ACT: Connect a route with leading and trailing whitespace
    r.connect("  spaced_cmd  ", dummy_controller_no_doc)

    # ASSERT: The stripped version should be registered
    assert "spaced_cmd" in r.routes

def test_router_connect_duplicate_raises_value_error() -> None:
    """Connecting an already registered route must raise a ``ValueError``."""

    # ARRANGE: Create a new router instance and register a route
    r = router.Router()
    r.connect("cmd", dummy_controller_no_doc)

    # ACT & ASSERT: Attempting to connect the same route raises an error
    with pytest.raises(ValueError, match="route already exists"):
        r.connect("cmd", dummy_controller_with_doc)


# =============================================================================
# Tests: Router.locate (Route dispatch)
# =============================================================================

def test_router_locate_returns_registered_controller() -> None:
    """Locating a registered route must return the exact controller callable bound to it."""

    # ARRANGE: Create a new router instance and register a route
    r = router.Router()
    r.connect("cmd", dummy_controller_with_doc)

    # ACT: Locate the associated controller
    controller = r.locate("cmd")

    # ASSERT: The returned controller must match the one initially connected
    assert controller is dummy_controller_with_doc

def test_router_locate_raises_router_error_if_unknown() -> None:
    """Locating an unknown or unregistered route must raise a ``RouterError``."""

    # ARRANGE: Create an empty router instance
    r = router.Router()

    # ACT & ASSERT: Looking for an unmapped route triggers a standard wrapper exception
    with pytest.raises(config.RouterError, match="unknown"):
        r.locate("unknown")


# =============================================================================
# Tests: Router.routes (Property)
# =============================================================================

def test_router_routes_property_returns_all_registered_routes() -> None:
    """The routes property must return a tuple of all route strings in insertion order."""

    # ARRANGE: Create a new router instance and populate it with multiple entries
    r = router.Router()

    r.connect("alpha", dummy_controller_no_doc)
    r.connect("beta", dummy_controller_no_doc)

    # ACT: Retrieve the fully registered mapped tuple
    registered = r.routes

    # ASSERT: Should strictly match the exact names and exact sequence applied
    assert registered == ("alpha", "beta")


# =============================================================================
# Tests: Router.get_route_usage (Docstring formatting)
# =============================================================================

def test_router_get_route_usage_returns_formatted_docstring() -> None:
    """Retrieving route usage must return the controller's docstring collapsed into a single space-separated string."""

    # ARRANGE: Register a controller with a multi-line docstring
    r = router.Router()
    r.connect("cmd", dummy_controller_with_doc)

    # ACT: Extract its documentation mapping via the standardized utility function
    usage = r.get_route_usage("cmd")

    # ASSERT: Multi-line strings are stripped and padded correctly on spacing
    assert usage == "A dummy controller with a multi-line docstring."

def test_router_get_route_usage_returns_empty_string_when_no_docstring() -> None:
    """Retrieving route usage for a controller without a docstring must return an empty string."""

    # ARRANGE: Register a controller containing strictly empty documentation payload
    r = router.Router()
    r.connect("cmd", dummy_controller_no_doc)

    # ACT: Query documentation definition
    usage = r.get_route_usage("cmd")

    # ASSERT: Safely bounces back empty sequences
    assert usage == ""


# =============================================================================
# Tests: Router.documentation (Full help text property)
# =============================================================================

def test_router_documentation_property_formats_help_text() -> None:
    """The documentation property must format a help string for all routes, aligned by the longest route name."""

    # ARRANGE: Create a new router instance and connect commands with varied lengths
    r = router.Router()
    r.connect("ls", dummy_controller_no_doc)
    r.connect("execute", dummy_controller_with_doc)

    # ACT: Generate the full documentation ledger text body
    docs = r.documentation

    # ASSERT: Inspect the layout spacing constraints strictly enforcing padding alignments
    expected_ls_line = "ls      : "
    expected_execute_line = "execute : A dummy controller with a multi-line docstring."

    assert expected_ls_line in docs
    assert expected_execute_line in docs

def test_router_documentation_property_returns_empty_string_if_no_routes() -> None:
    """The documentation property must return an empty string if no routes are registered."""

    # ARRANGE: Prepare empty state parser table
    r = router.Router()

    # ACT: Check output fallback handling routine
    docs = r.documentation

    # ASSERT: Handled transparently without key calculation issues
    assert docs == ""
