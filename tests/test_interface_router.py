"""Tests for the ``declusor.interface.router`` module."""

import pytest

from declusor.interface import connection, console, router


# =============================================================================
# Dummies/Mocks
# =============================================================================

class DummyRouter(router.IRouter):
    """Null-implementation subclass delegating attributes to the interface."""

    @property
    def routes(self) -> tuple[str, ...]:
        return super().routes

    @property
    def documentation(self) -> str:
        return super().documentation

    def get_route_usage(self, route: str) -> str:
        return super().get_route_usage(route)

    def connect(self, route: str, controller) -> None:
        super().connect(route, controller)

    def locate(self, route: str):
        return super().locate(route)


# =============================================================================
# Tests: IRouter (Interface contract)
# =============================================================================

def test_irouter_properties_raise_not_implemented_error() -> None:
    """Accessing abstract properties on ``IRouter`` must raise a ``NotImplementedError``."""

    # ARRANGE: Dummy routing object wrapper
    dummy = DummyRouter()

    # ACT & ASSERT: Validate generic exceptions signal missing implementations successfully
    with pytest.raises(NotImplementedError):
        _ = dummy.routes

    with pytest.raises(NotImplementedError):
        _ = dummy.documentation

def test_irouter_methods_raise_not_implemented_error() -> None:
    """Calling abstract route methods on ``IRouter`` must raise a ``NotImplementedError``."""

    # ARRANGE: Dummy framework wrapper
    dummy = DummyRouter()

    def dummy_controller(conn: connection.IConnection, term: console.IConsole, arg: str) -> None:
        pass

    # ACT & ASSERT: Target behavior explicitly throws the missing hook error
    with pytest.raises(NotImplementedError):
        dummy.get_route_usage("cmd")

    with pytest.raises(NotImplementedError):
        dummy.connect("cmd", dummy_controller)

    with pytest.raises(NotImplementedError):
        dummy.locate("cmd")
