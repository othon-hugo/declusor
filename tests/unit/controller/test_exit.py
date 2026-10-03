"""Unit tests for ExitArguments and call_exit in declusor.controller.exit."""

from typing import is_typeddict

from declusor import contract, testing
from declusor.controller import exit as exit_module


class TestExitArguments:
    """Tests verifying ExitArguments TypedDict invariants and contract compliance."""

    def test_exit_arguments__is_typeddict(self) -> None:
        """ExitArguments is a valid TypedDict type."""

        assert is_typeddict(exit_module.ExitArguments)

    def test_exit_arguments__total_is_false(self) -> None:
        """ExitArguments declares total=False allowing empty argument mappings."""

        assert exit_module.ExitArguments.__total__ is False

    def test_exit_arguments__instantiation__accepts_empty_mapping(self) -> None:
        """An empty mapping satisfies ExitArguments."""

        empty_args: exit_module.ExitArguments = {}

        assert isinstance(empty_args, dict)
        assert len(empty_args) == 0


class TestExitController:
    """Tests verifying call_exit controller behavior and termination signals."""

    def test_call_exit__standard_empty_request__returns_termination_result(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """call_exit returns a ControllerResult with action=TERMINATE on empty request."""

        req = testing.create_dummy_controller_request("", exit_module.ExitArguments)

        result = exit_module.call_exit(test_session, req)

        assert isinstance(result, contract.ControllerResult)
        assert result.action == contract.ControllerAction.TERMINATE

    def test_call_exit__extraneous_arguments__ignores_tokens_and_returns_termination_result(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """call_exit terminates the session cleanly even when extraneous arguments are supplied."""

        req = testing.create_dummy_controller_request("now --force 123", exit_module.ExitArguments)

        result = exit_module.call_exit(test_session, req)

        assert isinstance(result, contract.ControllerResult)
        assert result.action == contract.ControllerAction.TERMINATE

    def test_call_exit__execution__leaves_session_and_connection_unmodified(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
    ) -> None:
        """call_exit produces no writes to connection and records no view output."""

        req = testing.create_dummy_controller_request("", exit_module.ExitArguments)

        exit_module.call_exit(test_session, req)

        assert dummy_connection.written == []
        assert dummy_view.messages == []
        assert dummy_view.errors == []
