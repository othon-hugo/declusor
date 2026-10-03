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
                self._routes: dict[str, contract.Controller] = {}

            @property
            def routes(self) -> Sequence[str]:
                return tuple(self._routes.keys())

            def help(self, route: str, /) -> str:
                target = self._routes.get(route)
                if target is not None and target.__doc__:
                    return target.__doc__.strip().splitlines()[0]
                return ""

            def connect(self, route: str, controller: contract.Controller, /) -> None:
                self._routes[route] = controller

            def locate(self, route: str, /) -> contract.Controller:
                return self._routes[route]

        router = _ConcreteRouter()

        assert isinstance(router, contract.IRouter)
        assert len(router.routes) == 0

        router.connect("sample", _sample_controller)
        assert tuple(router.routes) == ("sample",)
        assert router.locate("sample") is _sample_controller
        assert router.help("sample") == "Execute sample operation."


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

    def test_dummy_router__help__extracts_first_line_of_controller_docstring(self) -> None:
        """Verify DummyRouter extracts the first docstring line as usage help."""

        router = DummyRouter()
        router.connect("sample", _sample_controller)

        assert router.help("sample") == "Execute sample operation."

    def test_dummy_router__help_unregistered_route__returns_empty_string(self) -> None:
        """Verify DummyRouter returns an empty string when route is not registered."""

        router = DummyRouter()

        assert router.help("nonexistent") == ""

    def test_dummy_router__positional_only_arguments__reject_keyword_passing(self) -> None:
        """Verify connect, locate, and help enforce positional-only contracts."""

        router = DummyRouter()

        with pytest.raises(TypeError, match="positional-only"):
            router.connect(route="sample", controller=_sample_controller)  # type: ignore[call-arg]

        with pytest.raises(TypeError, match="positional-only"):
            router.locate(route="sample")  # type: ignore[call-arg]

        with pytest.raises(TypeError, match="positional-only"):
            router.help(route="sample")  # type: ignore[call-arg]
