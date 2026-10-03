"""Unit tests for PromptLoop signal handling, exceptions, and defensive guards in declusor.presentation.prompt."""

import pytest

from declusor import config, contract, presentation, testing


def _terminate_controller(
    session: contract.SessionContext,
    request: contract.IControllerRequest[contract.ControllerArguments],
    /,
) -> contract.ControllerResult:
    """Terminate the prompt loop."""

    return contract.ControllerResult(action=contract.ControllerAction.TERMINATE)


class TestPromptLoopKeyboardInterrupt:
    """Tests verifying KeyboardInterrupt handling during operator input and command execution."""

    def test_prompt_loop_keyboard_interrupt_during_input__terminates_loop_gracefully(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
        dummy_view: testing.DummyView,
    ) -> None:
        """KeyboardInterrupt while waiting for operator input exits the prompt loop cleanly."""

        dummy_input_source.input_exception = KeyboardInterrupt()

        prompt = presentation.PromptLoop(
            "test_cli",
            router=dummy_router,
            session=test_session,
        )
        prompt.run()

        assert dummy_view.errors == []
        assert dummy_router.locate_calls == []

    def test_prompt_loop_eof_error_during_input__terminates_loop_gracefully(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
        dummy_view: testing.DummyView,
    ) -> None:
        """EOFError while waiting for operator input exits the prompt loop cleanly without error."""

        dummy_input_source.input_exception = EOFError()

        prompt = presentation.PromptLoop(
            "test_cli",
            router=dummy_router,
            session=test_session,
        )
        prompt.run()

        assert dummy_view.errors == []
        assert dummy_router.locate_calls == []

    def test_prompt_loop_keyboard_interrupt_during_controller_execution__skips_to_next_iteration(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
        dummy_view: testing.DummyView,
    ) -> None:
        """KeyboardInterrupt during command execution catches the interrupt and continues loop."""

        dummy_input_source.feed_inputs("interrupt_cmd", "exit")

        def interrupting_controller(
            session: contract.SessionContext,
            req: contract.IControllerRequest[contract.ControllerArguments],
        ) -> contract.ControllerResult:
            raise KeyboardInterrupt()

        dummy_router.connect("interrupt_cmd", interrupting_controller)
        dummy_router.connect("exit", _terminate_controller)

        prompt = presentation.PromptLoop(
            "test_cli",
            router=dummy_router,
            session=test_session,
        )
        prompt.run()

        assert dummy_view.errors == []
        assert dummy_router.locate_calls == ["interrupt_cmd", "exit"]


class TestPromptLoopConnectionClosed:
    """Tests verifying ConnectionClosed signal handling and graceful session teardown."""

    def test_prompt_loop_connection_closed_during_execution__writes_error_and_terminates_session(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
        dummy_view: testing.DummyView,
    ) -> None:
        """ConnectionClosed writes error to view and immediately terminates session without re-prompting."""

        dummy_input_source.feed_inputs("disconnect_cmd", "unreachable_cmd")
        closed_exc = config.ConnectionClosed("Peer closed socket transport.")

        def disconnect_controller(
            session: contract.SessionContext,
            req: contract.IControllerRequest[contract.ControllerArguments],
        ) -> contract.ControllerResult:
            raise closed_exc

        dummy_router.connect("disconnect_cmd", disconnect_controller)

        prompt = presentation.PromptLoop(
            "test_cli",
            router=dummy_router,
            session=test_session,
        )
        prompt.run()

        assert dummy_view.errors == [closed_exc]
        assert dummy_router.locate_calls == ["disconnect_cmd"]


class TestPromptLoopDeclusorException:
    """Tests verifying DeclusorException recovery and error output to presentation view."""

    def test_prompt_loop_unknown_route__writes_router_error_and_continues_loop(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
        dummy_view: testing.DummyView,
    ) -> None:
        """Unknown route dispatches RouterError to view and continues processing next command."""

        dummy_input_source.feed_inputs("nonexistent_command", "exit")
        dummy_router.connect("exit", _terminate_controller)

        prompt = presentation.PromptLoop(
            "test_cli",
            router=dummy_router,
            session=test_session,
        )
        prompt.run()

        assert len(dummy_view.errors) == 1
        assert isinstance(dummy_view.errors[0], config.RouterError)
        assert "invalid route: 'nonexistent_command'" in str(dummy_view.errors[0])
        assert dummy_router.locate_calls == ["nonexistent_command", "exit"]

    def test_prompt_loop_command_error__writes_error_and_continues_loop(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
        dummy_view: testing.DummyView,
    ) -> None:
        """CommandError raised by a controller writes error to view and continues loop."""

        dummy_input_source.feed_inputs("failing_cmd", "exit")
        cmd_exc = config.CommandError("Failed to parse binary command payload.")

        def fail_controller(
            session: contract.SessionContext,
            req: contract.IControllerRequest[contract.ControllerArguments],
        ) -> contract.ControllerResult:
            raise cmd_exc

        dummy_router.connect("failing_cmd", fail_controller)
        dummy_router.connect("exit", _terminate_controller)

        prompt = presentation.PromptLoop(
            "test_cli",
            router=dummy_router,
            session=test_session,
        )
        prompt.run()

        assert dummy_view.errors == [cmd_exc]
        assert dummy_router.locate_calls == ["failing_cmd", "exit"]

    def test_prompt_loop_parser_error__writes_error_and_continues_loop(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
        dummy_view: testing.DummyView,
    ) -> None:
        """ParserError raised by argument parsing writes error to view and continues loop."""

        dummy_input_source.feed_inputs("parse_err_cmd", "exit")
        parser_exc = config.ParserError("unrecognized arguments: --bogus")

        def parse_err_controller(
            session: contract.SessionContext,
            req: contract.IControllerRequest[contract.ControllerArguments],
        ) -> contract.ControllerResult:
            raise parser_exc

        dummy_router.connect("parse_err_cmd", parse_err_controller)
        dummy_router.connect("exit", _terminate_controller)

        prompt = presentation.PromptLoop(
            "test_cli",
            router=dummy_router,
            session=test_session,
        )
        prompt.run()

        assert dummy_view.errors == [parser_exc]
        assert dummy_router.locate_calls == ["parse_err_cmd", "exit"]

    def test_prompt_loop_invalid_operation__writes_error_and_continues_loop(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
        dummy_view: testing.DummyView,
    ) -> None:
        """InvalidOperation raised during execution writes error to view and continues loop."""

        dummy_input_source.feed_inputs("invalid_op_cmd", "exit")
        invalid_op_exc = config.InvalidOperation("Action forbidden in active session state.")

        def invalid_op_controller(
            session: contract.SessionContext,
            req: contract.IControllerRequest[contract.ControllerArguments],
        ) -> contract.ControllerResult:
            raise invalid_op_exc

        dummy_router.connect("invalid_op_cmd", invalid_op_controller)
        dummy_router.connect("exit", _terminate_controller)

        prompt = presentation.PromptLoop(
            "test_cli",
            router=dummy_router,
            session=test_session,
        )
        prompt.run()

        assert dummy_view.errors == [invalid_op_exc]
        assert dummy_router.locate_calls == ["invalid_op_cmd", "exit"]

    def test_prompt_loop_controller_error__writes_error_and_continues_loop(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
        dummy_view: testing.DummyView,
    ) -> None:
        """ControllerError raised during execution writes error to view and continues loop."""

        dummy_input_source.feed_inputs("ctrl_err_cmd", "exit")
        ctrl_exc = config.ControllerError("Argument parsing failure")

        def ctrl_err_controller(
            session: contract.SessionContext,
            req: contract.IControllerRequest[contract.ControllerArguments],
        ) -> contract.ControllerResult:
            raise ctrl_exc

        dummy_router.connect("ctrl_err_cmd", ctrl_err_controller)
        dummy_router.connect("exit", _terminate_controller)

        prompt = presentation.PromptLoop(
            "test_cli",
            router=dummy_router,
            session=test_session,
        )
        prompt.run()

        assert dummy_view.errors == [ctrl_exc]
        assert dummy_router.locate_calls == ["ctrl_err_cmd", "exit"]


class TestPromptLoopDefensiveGuards:
    """Tests verifying internal defensive guards in PromptLoop subroutines."""

    def test_prompt_loop_read_command_when_session_input_is_none__raises_invalid_operation(
        self,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """_read_command defends against session input dynamically becoming None."""

        session_without_input = contract.SessionContext(
            connection=dummy_connection,
            view=dummy_view,
            plugin_processor=dummy_file_store,
            input_source=None,
        )
        prompt = presentation.PromptLoop()

        with pytest.raises(config.InvalidOperation, match="Input source is not available"):
            prompt._read_command(session_without_input)

    def test_prompt_loop_route_command_empty_string__raises_prompt_error(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
    ) -> None:
        """_route_command raises PromptError when command_line is an empty string."""

        prompt = presentation.PromptLoop(router=dummy_router, session=test_session)

        with pytest.raises(config.PromptError, match="empty route"):
            prompt._route_command("", test_session, dummy_router)

    def test_prompt_loop_route_command_whitespace_only__raises_prompt_error(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
    ) -> None:
        """_route_command raises PromptError when command_line is whitespace only."""

        prompt = presentation.PromptLoop(router=dummy_router, session=test_session)

        with pytest.raises(config.PromptError, match="empty route"):
            prompt._route_command("   \t\n  ", test_session, dummy_router)

    def test_prompt_loop_route_command_empty_tokens__raises_prompt_error(
        self,
        dummy_router: testing.DummyRouter,
        test_session: contract.SessionContext,
    ) -> None:
        """_route_command raises PromptError when token splitting yields an invalid structure."""

        class EmptyTokensString(str):
            def strip(self, *args: object, **kwargs: object) -> "EmptyTokensString":
                return self

            def split(self, *args: object, **kwargs: object) -> list[str]:
                return []

        prompt = presentation.PromptLoop(router=dummy_router, session=test_session)
        invalid_line = EmptyTokensString("bad_line")

        with pytest.raises(config.PromptError, match="invalid command"):
            prompt._route_command(invalid_line, test_session, dummy_router)
