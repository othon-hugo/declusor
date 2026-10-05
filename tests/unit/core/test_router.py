"""Unit tests for the core Router component in declusor.core.router."""

import pytest

from declusor import config, contract, core


def _sample_controller(
    session: contract.SessionContext,
    request: contract.IControllerRequest[contract.ControllerArguments],
    /,
) -> contract.ControllerResult:
    """Execute sample operation for testing."""

    return contract.ControllerResult.for_continuation()


class TestRouterRegistration:
    """Tests verifying route registration invariants on Router."""

    def test_router__connect_valid_route__registers_in_routes_tuple(self) -> None:
        """Connecting a controller registers the route in the routes sequence."""

        router = core.Router()

        router.connect("sample", _sample_controller)

        assert router.routes == ("sample",)
        assert "sample" in router.routes

    def test_router__connect_whitespace_padded_route__strips_whitespace_on_registration(self) -> None:
        """Surrounding whitespace is stripped from route names during registration."""

        router = core.Router()

        router.connect("   sample   ", _sample_controller)

        assert router.routes == ("sample",)
        assert router.locate("sample") is _sample_controller

    def test_router__connect_duplicate_route__raises_duplicate_route_error(self) -> None:
        """Registering an existing route name raises DuplicateRouteError."""

        router = core.Router()
        router.connect("sample", _sample_controller)

        with pytest.raises(config.DuplicateRouteError) as exc_info:
            router.connect("sample", _sample_controller)

        assert exc_info.value.route == "sample"
        assert isinstance(exc_info.value, ValueError)
        assert isinstance(exc_info.value, config.RouterError)

    def test_router__connect_duplicate_route_with_differing_whitespace__raises_duplicate_route_error(self) -> None:
        """Duplicate detection operates on stripped route strings."""

        router = core.Router()
        router.connect("sample", _sample_controller)

        with pytest.raises(config.DuplicateRouteError) as exc_info:
            router.connect("   sample \t ", _sample_controller)

        assert exc_info.value.route == "sample"

    def test_router__connect_multiple_routes__preserves_insertion_order(self) -> None:
        """Router maintains strict insertion order across multiple connected routes."""

        router = core.Router()

        router.connect("first", _sample_controller)
        router.connect("second", _sample_controller)
        router.connect("third", _sample_controller)

        assert router.routes == ("first", "second", "third")

    def test_router__routes_property__returns_immutable_tuple(self) -> None:
        """The routes property exposes an immutable tuple."""

        router = core.Router()
        router.connect("alpha", _sample_controller)

        routes = router.routes

        assert isinstance(routes, tuple)
        assert routes == ("alpha",)

    def test_router__connect_positional_only__rejects_keyword_arguments(self) -> None:
        """The connect method enforces positional-only parameters."""

        router = core.Router()

        with pytest.raises(TypeError, match="positional-only"):
            router.connect(route="sample", controller=_sample_controller)  # type: ignore[call-arg]


class TestRouterResolution:
    """Tests verifying controller resolution invariants on Router."""

    def test_router__locate_existing_route__returns_registered_controller(self) -> None:
        """Locating an existing route returns the bound controller."""

        router = core.Router()
        router.connect("sample", _sample_controller)

        controller = router.locate("sample")

        assert controller is _sample_controller

    def test_router__locate_whitespace_padded_route__resolves_stripped_route(self) -> None:
        """Locating handles whitespace padding gracefully by stripping lookup keys."""

        router = core.Router()
        router.connect("sample", _sample_controller)

        assert router.locate("   sample   ") is _sample_controller
        assert router.locate("\tsample\n") is _sample_controller

    def test_router__locate_unknown_route__raises_router_error(self) -> None:
        """Locating an unregistered route name raises RouterError."""

        router = core.Router()

        with pytest.raises(config.RouterError) as exc_info:
            router.locate("unregistered")

        assert exc_info.value.route == "unregistered"

    def test_router__locate_unknown_route__populates_exception_route_attribute(self) -> None:
        """RouterError records the requested route name for unknown routes."""

        router = core.Router()

        with pytest.raises(config.RouterError) as exc_info:
            router.locate("missing")

        assert exc_info.value.route == "missing"

    def test_router__locate_positional_only__rejects_keyword_arguments(self) -> None:
        """The locate method enforces positional-only parameters."""

        router = core.Router()
        router.connect("sample", _sample_controller)

        with pytest.raises(TypeError, match="positional-only"):
            router.locate(route="sample")  # type: ignore[call-arg]

    def test_router__locate_case_sensitive__does_not_match_differing_case(self) -> None:
        """Route resolution is case-sensitive and does not match uppercase variants."""

        router = core.Router()
        router.connect("sample", _sample_controller)

        with pytest.raises(config.RouterError) as exc_info:
            router.locate("SAMPLE")

        assert exc_info.value.route == "SAMPLE"


class TestRouterHelp:
    """Tests verifying explicit route help metadata on Router."""

    def test_router__help_explicit_metadata__returns_short_and_complement(self) -> None:
        """Help returns metadata from the route registration, not the controller docstring."""

        router = core.Router()
        registration = contract.RouteRegistration(_sample_controller, contract.RouteHelp("Short help.", "Detailed help."))
        router.connect("sample", registration)

        assert router.help("sample") == contract.RouteHelp("Short help.", "Detailed help.")

    def test_router__help_same_controller_on_distinct_routes__keeps_route_help_independent(self) -> None:
        """A shared controller may have different help metadata per route."""

        router = core.Router()
        router.connect("first", contract.RouteRegistration(_sample_controller, contract.RouteHelp("First.")))
        router.connect("second", contract.RouteRegistration(_sample_controller, contract.RouteHelp("Second.")))

        assert router.help("first") == contract.RouteHelp("First.")
        assert router.help("second") == contract.RouteHelp("Second.")

    def test_router__help_without_metadata__ignores_controller_docstring(self) -> None:
        """Direct controller registration produces empty help despite a controller docstring."""

        router = core.Router()
        router.connect("undoc", _sample_controller)

        assert router.help("undoc") == contract.RouteHelp()

    def test_router__help_whitespace_padded_route__resolves_and_returns_help(self) -> None:
        """Help strips surrounding whitespace when looking up routes."""

        router = core.Router()
        router.connect("sample", contract.RouteRegistration(_sample_controller, contract.RouteHelp("Sample.")))

        assert router.help("   sample   ") == contract.RouteHelp("Sample.")

    def test_router__help_unregistered_route__raises_router_error(self) -> None:
        """Help raises RouterError when querying an unregistered route."""

        router = core.Router()

        with pytest.raises(config.RouterError) as exc_info:
            router.help("nonexistent")

        assert exc_info.value.route == "nonexistent"

    def test_router__help_positional_only__rejects_keyword_arguments(self) -> None:
        """The help method enforces positional-only parameters."""

        router = core.Router()
        router.connect("sample", _sample_controller)

        with pytest.raises(TypeError, match="positional-only"):
            router.help(route="sample")  # type: ignore[call-arg]


class TestRouterContractConformance:
    """Tests verifying Router conforms to the IRouter abstract contract."""

    def test_router__isinstance__conforms_to_irouter_contract(self) -> None:
        """Router is an instance and subclass of IRouter."""

        router = core.Router()

        assert isinstance(router, contract.IRouter)
        assert issubclass(core.Router, contract.IRouter)
