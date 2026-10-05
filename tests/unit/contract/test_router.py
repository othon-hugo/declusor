"""Unit tests for router contract and interface specifications."""

from collections.abc import Sequence

import pytest

from declusor import contract
from declusor.testing import DummyRouter


def _sample_controller(
    session: contract.SessionContext,
    request: contract.IControllerRequest[contract.ControllerArguments],
) -> contract.ControllerResult:
    """Execute sample operation.

    Extended documentation details.
    """

    return contract.ControllerResult.for_continuation()


class TestIRouter:
    """Tests for IRouter abstract base class and interface contract."""

    def test_irouter__direct_instantiation__raises_type_error(self) -> None:
        """Verify IRouter cannot be instantiated directly without implementations."""

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            contract.IRouter()  # type: ignore[abstract]

    def test_irouter__incomplete_subclass__raises_type_error(self) -> None:
        """Verify subclass lacking abstract methods cannot be instantiated."""

        class _IncompleteRouter(contract.IRouter):
            """Subclass omitting required abstract methods."""

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            _IncompleteRouter()  # type: ignore[abstract]

    def test_irouter__concrete_subclass__satisfies_abstract_contract(self) -> None:
        """Verify minimal concrete subclass fulfills IRouter interface contract."""

        class _ConcreteRouter(contract.IRouter):
            """Minimal concrete implementation of IRouter."""

            def __init__(self) -> None:
                self._routes: dict[str, contract.RouteRegistration] = {}

            @property
            def routes(self) -> Sequence[str]:
                return tuple(self._routes.keys())

            def help(self, route: str, /) -> contract.RouteHelp:
                registration = self._routes.get(route)
                return registration.help if registration is not None else contract.RouteHelp()

            def connect(self, route: str, registration: contract.RouteRegistration, /) -> None:
                self._routes[route] = registration

            def locate(self, route: str, /) -> contract.Controller:
                return self._routes[route].controller

        router = _ConcreteRouter()

        assert isinstance(router, contract.IRouter)
        assert len(router.routes) == 0

        registration = contract.RouteRegistration(_sample_controller, contract.RouteHelp("Sample.", "More details."))
        router.connect("sample", registration)
        assert tuple(router.routes) == ("sample",)
        assert router.locate("sample") is _sample_controller
        assert router.help("sample") == contract.RouteHelp("Sample.", "More details.")


class TestDummyRouterContract:
    """Tests verifying DummyRouter conforms to the IRouter contract."""

    def test_dummy_router__subclass_and_isinstance__conforms_to_irouter(self) -> None:
        """Verify DummyRouter is a subclass and instance of IRouter."""

        router = DummyRouter()

        assert issubclass(DummyRouter, contract.IRouter)
        assert isinstance(router, contract.IRouter)

    def test_dummy_router__empty_state__returns_empty_routes_sequence(self) -> None:
        """Verify fresh DummyRouter returns an empty sequence of registered routes."""

        router = DummyRouter()

        assert router.routes == ()

    def test_dummy_router__connect_and_locate__registers_and_resolves_controller(self) -> None:
        """Verify DummyRouter connects and locates registered controllers."""

        router = DummyRouter()
        router.connect("sample", _sample_controller)

        assert "sample" in router.routes
        assert router.locate("sample") is _sample_controller

    def test_dummy_router__help__returns_explicit_registration_metadata(self) -> None:
        """Verify DummyRouter returns help metadata stored in a route registration."""

        router = DummyRouter()
        registration = contract.RouteRegistration(_sample_controller, contract.RouteHelp("Short.", "Long."))
        router.connect("sample", registration)

        assert router.help("sample") == contract.RouteHelp("Short.", "Long.")

    def test_dummy_router__help_unregistered_route__returns_empty_help(self) -> None:
        """Verify DummyRouter returns empty metadata when route is not registered."""

        router = DummyRouter()

        assert router.help("nonexistent") == contract.RouteHelp()

    def test_dummy_router__positional_only_arguments__reject_keyword_passing(self) -> None:
        """Verify connect, locate, and help enforce positional-only contracts."""

        router = DummyRouter()

        with pytest.raises(TypeError, match="positional-only"):
            router.connect(route="sample", registration=contract.RouteRegistration(_sample_controller, contract.RouteHelp()))  # type: ignore[call-arg]

        with pytest.raises(TypeError, match="positional-only"):
            router.locate(route="sample")  # type: ignore[call-arg]

        with pytest.raises(TypeError, match="positional-only"):
            router.help(route="sample")  # type: ignore[call-arg]
