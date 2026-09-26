import pytest

from declusor import config, contract, core


def test_router_connect_and_locate() -> None:
    """Verify route registration and lookup."""

    router = core.Router()

    def dummy_controller(
        dependencies: contract.SessionContext,
        argument: contract.ControllerRequest,
    ) -> contract.ControllerResult:
        return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)

    router.connect("test", dummy_controller)

    assert "test" in router.routes
    assert router.locate("test") is dummy_controller
    # Whitespace stripping
    assert router.locate("  test  ") is dummy_controller


def test_router_duplicate_connect_raises_value_error() -> None:
    """Verify registering the same route twice raises ValueError."""

    router = core.Router()

    def dummy_controller(
        dependencies: contract.SessionContext,
        argument: contract.ControllerRequest,
    ) -> contract.ControllerResult:
        return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)

    router.connect("test", dummy_controller)

    with pytest.raises(ValueError, match="route already exists"):
        router.connect("test", dummy_controller)


def test_router_locate_unknown_raises_router_error() -> None:
    """Verify looking up unregistered route raises RouterError."""

    router = core.Router()

    with pytest.raises(config.RouterError) as exc_info:
        router.locate("unknown_cmd")

    assert exc_info.value.route == "unknown_cmd"


def test_router_get_route_usage() -> None:
    """Verify route usage extraction from controller docstrings."""

    router = core.Router()

    def cmd_a(
        dependencies: contract.SessionContext,
        argument: contract.ControllerRequest,
    ) -> contract.ControllerResult:
        """First command description."""

        return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)

    def cmd_b(
        dependencies: contract.SessionContext,
        argument: contract.ControllerRequest,
    ) -> contract.ControllerResult:
        """Second command
        with multiple lines.
        """

        return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)

    router.connect("alpha", cmd_a)
    router.connect("beta", cmd_b)

    assert router.get_route_usage("alpha") == "First command description."
    assert router.get_route_usage("beta") == "Second command with multiple lines."


def test_router_get_route_usage_empty_when_no_docstring() -> None:
    """Verify empty string returned when controller has no docstring."""

    router = core.Router()

    def no_doc_cmd(
        dependencies: contract.SessionContext,
        argument: contract.ControllerRequest,
    ) -> contract.ControllerResult:
        return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)

    router.connect("nodoc", no_doc_cmd)
    assert router.get_route_usage("nodoc") == ""
