"""Unit tests for HelpArguments and create_help_controller in declusor.controller.help."""

from typing import is_typeddict

from declusor import contract, testing
from declusor.controller import help as help_module


def _make_dummy_controller(description: str = "") -> contract.Controller:
    """Helper to construct dummy controller callables with docstrings."""

    def dummy(
        session: contract.SessionContext,
        req: contract.IControllerRequest[contract.ControllerArguments],
    ) -> contract.ControllerResult:
        return contract.ControllerResult.for_continuation()

    dummy.__doc__ = description
    return dummy


def _register_help_route(
    router: testing.DummyRouter,
    route: str,
    short: str = "",
    complement: str = "",
    controller_description: str = "",
) -> None:
    registration = contract.RouteRegistration(
        _make_dummy_controller(controller_description),
        contract.RouteHelp(short, complement),
    )
    router.connect(route, registration)


class TestHelpArguments:
    """Tests verifying HelpArguments TypedDict invariants and contract compliance."""

    def test_help_arguments__is_typeddict(self) -> None:
        """HelpArguments is a valid TypedDict type."""

        assert is_typeddict(help_module.HelpArguments)

    def test_help_arguments__total_is_false(self) -> None:
        """HelpArguments declares total=False allowing optional command route."""

        assert help_module.HelpArguments.__total__ is False

    def test_help_arguments__declares_command_field(self) -> None:
        """HelpArguments specifies command attribute as optional string."""

        assert "command" in help_module.HelpArguments.__annotations__


class TestCreateHelpController:
    """Tests verifying create_help_controller factory output and controller lifecycle."""

    def test_create_help_controller__returns_callable_controller(
        self,
        dummy_router: testing.DummyRouter,
    ) -> None:
        """create_help_controller returns a callable conforming to contract.Controller."""

        controller_fn = help_module.create_help_controller(dummy_router)

        assert callable(controller_fn)


class TestHelpControllerInvocation:
    """Tests verifying call_help route formatting, command lookup, and view outputs."""

    def test_call_help__all_routes_with_usage__formats_aligned_columns(
        self,
        test_session: contract.SessionContext,
        dummy_view: testing.DummyView,
        dummy_router: testing.DummyRouter,
    ) -> None:
        """call_help without arguments displays all registered routes aligned with usage descriptions."""

        _register_help_route(dummy_router, "cat", "Display file contents.")
        _register_help_route(dummy_router, "download", "Fetch remote asset.")

        help_ctrl = help_module.create_help_controller(dummy_router)
        req = testing.create_dummy_controller_request("", help_module.HelpArguments)

        result = help_ctrl(test_session, req)

        assert isinstance(result, contract.ControllerResult)
        assert result.action == contract.ControllerAction.CONTINUE
        assert dummy_view.messages == [
            "cat      : Display file contents.",
            "download : Fetch remote asset.",
        ]

    def test_call_help__routes_without_usage__displays_route_name_only(
        self,
        test_session: contract.SessionContext,
        dummy_view: testing.DummyView,
        dummy_router: testing.DummyRouter,
    ) -> None:
        """call_help lists route names without trailing colon or spaces when usage is absent."""

        _register_help_route(dummy_router, "ping")

        help_ctrl = help_module.create_help_controller(dummy_router)
        req = testing.create_dummy_controller_request("", help_module.HelpArguments)

        result = help_ctrl(test_session, req)

        assert result.action == contract.ControllerAction.CONTINUE
        assert dummy_view.messages == ["ping"]

    def test_call_help__mixed_routes_with_and_without_usage__formats_each_correctly(
        self,
        test_session: contract.SessionContext,
        dummy_view: testing.DummyView,
        dummy_router: testing.DummyRouter,
    ) -> None:
        """call_help handles a mix of documented and undocumented routes accurately."""

        _register_help_route(dummy_router, "echo", "Print string.")
        _register_help_route(dummy_router, "noop")

        help_ctrl = help_module.create_help_controller(dummy_router)
        req = testing.create_dummy_controller_request("", help_module.HelpArguments)

        result = help_ctrl(test_session, req)

        assert result.action == contract.ControllerAction.CONTINUE
        assert dummy_view.messages == [
            "echo : Print string.",
            "noop",
        ]

    def test_call_help__empty_router__writes_no_commands_notice(
        self,
        test_session: contract.SessionContext,
        dummy_view: testing.DummyView,
        dummy_router: testing.DummyRouter,
    ) -> None:
        """call_help writes a notice when router has no registered routes."""

        help_ctrl = help_module.create_help_controller(dummy_router)
        req = testing.create_dummy_controller_request("", help_module.HelpArguments)

        result = help_ctrl(test_session, req)

        assert result.action == contract.ControllerAction.CONTINUE
        assert dummy_view.messages == ["No commands available."]

    def test_call_help__specific_command_with_help__displays_short_and_complement(
        self,
        test_session: contract.SessionContext,
        dummy_view: testing.DummyView,
        dummy_router: testing.DummyRouter,
    ) -> None:
        """call_help displays explicit short and detailed help without a command prefix."""

        _register_help_route(
            dummy_router,
            "upload",
            "Upload a local file.",
            "Usage: upload <filepath> [destination]. The destination is optional.",
            "Controller docstrings must not appear in help.",
        )

        help_ctrl = help_module.create_help_controller(dummy_router)
        req = testing.create_dummy_controller_request("upload", help_module.HelpArguments)

        result = help_ctrl(test_session, req)

        assert result.action == contract.ControllerAction.CONTINUE
        assert dummy_view.messages == ["Upload a local file.\n\nUsage: upload <filepath> [destination]. The destination is optional."]

    def test_call_help__specific_command_without_usage__displays_command_name_only(
        self,
        test_session: contract.SessionContext,
        dummy_view: testing.DummyView,
        dummy_router: testing.DummyRouter,
    ) -> None:
        """call_help with a specific undocumented command displays only the command name."""

        _register_help_route(dummy_router, "bare")

        help_ctrl = help_module.create_help_controller(dummy_router)
        req = testing.create_dummy_controller_request("bare", help_module.HelpArguments)

        result = help_ctrl(test_session, req)

        assert result.action == contract.ControllerAction.CONTINUE
        assert dummy_view.messages == ["bare"]

    def test_call_help__unknown_command__writes_error_to_view_and_continues(
        self,
        test_session: contract.SessionContext,
        dummy_view: testing.DummyView,
        dummy_router: testing.DummyRouter,
    ) -> None:
        """call_help writes an error message to view when the specified route does not exist."""

        help_ctrl = help_module.create_help_controller(dummy_router)
        req = testing.create_dummy_controller_request("nonexistent_route", help_module.HelpArguments)

        result = help_ctrl(test_session, req)

        assert result.action == contract.ControllerAction.CONTINUE
        assert len(dummy_view.errors) == 1
        assert "Unknown command: 'nonexistent_route'" in str(dummy_view.errors[0])
        assert "Type 'help' to list available commands." in str(dummy_view.errors[0])

    def test_call_help__command_with_surrounding_whitespace__strips_target_route(
        self,
        test_session: contract.SessionContext,
        dummy_view: testing.DummyView,
        dummy_router: testing.DummyRouter,
    ) -> None:
        """call_help strips leading and trailing whitespace from the command name argument."""

        _register_help_route(dummy_router, "status", "Report agent status.")

        help_ctrl = help_module.create_help_controller(dummy_router)
        req = testing.create_dummy_controller_request("   status   ", help_module.HelpArguments)

        result = help_ctrl(test_session, req)

        assert result.action == contract.ControllerAction.CONTINUE
        assert dummy_view.messages == ["Report agent status."]

    def test_call_help__dynamically_registered_routes__reflects_latest_router_state(
        self,
        test_session: contract.SessionContext,
        dummy_view: testing.DummyView,
        dummy_router: testing.DummyRouter,
    ) -> None:
        """call_help dynamically evaluates the router so subsequent route additions are reflected."""

        help_ctrl = help_module.create_help_controller(dummy_router)
        _register_help_route(dummy_router, "late_route", "Late route usage.")
        req = testing.create_dummy_controller_request("", help_module.HelpArguments)

        result = help_ctrl(test_session, req)

        assert result.action == contract.ControllerAction.CONTINUE
        assert dummy_view.messages == ["late_route : Late route usage."]
