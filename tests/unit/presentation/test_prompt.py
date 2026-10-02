import pytest

from declusor import config, contract, presentation, testing


def test_prompt_terminates_on_controller_terminate_action(
    dummy_router: testing.DummyRouter,
    test_session: contract.SessionContext,
    dummy_input_source: testing.DummyInputSource,
) -> None:
    """PromptLoop must stop cleanly when a controller signals ControllerAction.TERMINATE."""

    dummy_input_source.feed_inputs("exit")

    def exit_controller(
        session: contract.SessionContext,
        req: contract.IControllerRequest[contract.ControllerArguments],
    ) -> contract.ControllerResult:
        return contract.ControllerResult(action=contract.ControllerAction.TERMINATE)

    dummy_router.connect("exit", exit_controller)

    prompt = presentation.PromptLoop(
        "test_cli",
        router=dummy_router,
        session=test_session,
    )

    prompt.run()

    assert dummy_router.locate_calls == ["exit"]


def test_prompt_handles_keyboard_interrupt_on_input(
    dummy_router: testing.DummyRouter,
    test_session: contract.SessionContext,
    dummy_input_source: testing.DummyInputSource,
) -> None:
    """PromptLoop must terminate loop gracefully on KeyboardInterrupt during input."""

    dummy_input_source.input_exception = KeyboardInterrupt()

    prompt = presentation.PromptLoop(
        "test_cli",
        router=dummy_router,
        session=test_session,
    )

    prompt.run()


def test_prompt_handles_keyboard_interrupt_during_execution(
    dummy_router: testing.DummyRouter,
    test_session: contract.SessionContext,
    dummy_input_source: testing.DummyInputSource,
) -> None:
    """PromptLoop catches KeyboardInterrupt during command execution and continues."""

    dummy_input_source.feed_inputs("long_cmd", "exit")

    def interrupt_controller(
        session: contract.SessionContext,
        req: contract.IControllerRequest[contract.ControllerArguments],
    ) -> contract.ControllerResult:
        raise KeyboardInterrupt()

    def exit_controller(
        session: contract.SessionContext,
        req: contract.IControllerRequest[contract.ControllerArguments],
    ) -> contract.ControllerResult:
        return contract.ControllerResult(action=contract.ControllerAction.TERMINATE)

    dummy_router.connect("long_cmd", interrupt_controller)
    dummy_router.connect("exit", exit_controller)

    prompt = presentation.PromptLoop(
        "test_cli",
        router=dummy_router,
        session=test_session,
    )

    prompt.run()

    assert dummy_router.locate_calls == ["long_cmd", "exit"]


def test_prompt_handles_declusor_exception(
    dummy_router: testing.DummyRouter,
    test_session: contract.SessionContext,
    dummy_input_source: testing.DummyInputSource,
    dummy_view: testing.DummyView,
) -> None:
    """PromptLoop catches DeclusorException and prints error without terminating loop."""

    dummy_input_source.feed_inputs("fail_cmd", "exit")
    exc = config.CommandError("failed")

    def fail_controller(
        session: contract.SessionContext,
        req: contract.IControllerRequest[contract.ControllerArguments],
    ) -> contract.ControllerResult:
        raise exc

    def exit_controller(
        session: contract.SessionContext,
        req: contract.IControllerRequest[contract.ControllerArguments],
    ) -> contract.ControllerResult:
        return contract.ControllerResult(action=contract.ControllerAction.TERMINATE)

    dummy_router.connect("fail_cmd", fail_controller)
    dummy_router.connect("exit", exit_controller)

    prompt = presentation.PromptLoop(
        "test_cli",
        router=dummy_router,
        session=test_session,
    )

    prompt.run()

    assert exc in dummy_view.errors
    assert dummy_router.locate_calls == ["fail_cmd", "exit"]


def test_prompt_loop_as_session_runner(
    dummy_router: testing.DummyRouter,
    test_session: contract.SessionContext,
    dummy_input_source: testing.DummyInputSource,
) -> None:
    """PromptLoop can be instantiated standalone and executed via ISessionRunner.run(session, router)."""

    runner: contract.ISessionRunner = presentation.PromptLoop("test_cli")

    dummy_input_source.feed_inputs("quit")

    def quit_controller(
        session: contract.SessionContext,
        req: contract.IControllerRequest[contract.ControllerArguments],
    ) -> contract.ControllerResult:
        return contract.ControllerResult(action=contract.ControllerAction.TERMINATE)

    dummy_router.connect("quit", quit_controller)

    runner.run(test_session, dummy_router)

    assert dummy_router.locate_calls == ["quit"]


def test_prompt_handles_connection_closed_terminates_session(
    dummy_router: testing.DummyRouter,
    test_session: contract.SessionContext,
    dummy_input_source: testing.DummyInputSource,
    dummy_view: testing.DummyView,
) -> None:
    """PromptLoop catches ConnectionClosed, logs the error, and terminates session without re-prompting."""

    dummy_input_source.feed_inputs("disconnect_cmd", "never_reached")
    exc = config.ConnectionClosed("Peer terminated connection.")

    def disconnect_controller(
        session: contract.SessionContext,
        req: contract.IControllerRequest[contract.ControllerArguments],
    ) -> contract.ControllerResult:
        raise exc

    dummy_router.connect("disconnect_cmd", disconnect_controller)

    prompt = presentation.PromptLoop(
        "test_cli",
        router=dummy_router,
        session=test_session,
    )

    prompt.run()

    assert exc in dummy_view.errors
    assert dummy_router.locate_calls == ["disconnect_cmd"]


def test_prompt_missing_session_or_router_raises_invalid_operation() -> None:
    """PromptLoop raises InvalidOperation when run without session, router, or input source."""

    prompt = presentation.PromptLoop("test_cli")

    with pytest.raises(config.InvalidOperation, match="PromptLoop requires an active session and router"):
        prompt.run()


def test_prompt_displays_controller_result_message_on_continue(
    dummy_router: testing.DummyRouter,
    test_session: contract.SessionContext,
    dummy_input_source: testing.DummyInputSource,
    dummy_view: testing.DummyView,
) -> None:
    """PromptLoop must write message to view when controller returns ControllerResult with message."""

    dummy_input_source.feed_inputs("status", "exit")

    def status_controller(
        session: contract.SessionContext,
        req: contract.IControllerRequest[contract.ControllerArguments],
    ) -> contract.ControllerResult:
        return contract.ControllerResult(
            action=contract.ControllerAction.CONTINUE,
            message="Status operational.",
        )

    def exit_controller(
        session: contract.SessionContext,
        req: contract.IControllerRequest[contract.ControllerArguments],
    ) -> contract.ControllerResult:
        return contract.ControllerResult(action=contract.ControllerAction.TERMINATE)

    dummy_router.connect("status", status_controller)
    dummy_router.connect("exit", exit_controller)

    prompt = presentation.PromptLoop(
        "test_cli",
        router=dummy_router,
        session=test_session,
    )

    prompt.run()

    assert "Status operational." in dummy_view.messages


def test_prompt_displays_controller_result_message_on_terminate(
    dummy_router: testing.DummyRouter,
    test_session: contract.SessionContext,
    dummy_input_source: testing.DummyInputSource,
    dummy_view: testing.DummyView,
) -> None:
    """PromptLoop must write message to view before terminating when controller terminates with message."""

    dummy_input_source.feed_inputs("bye")

    def bye_controller(
        session: contract.SessionContext,
        req: contract.IControllerRequest[contract.ControllerArguments],
    ) -> contract.ControllerResult:
        return contract.ControllerResult(
            action=contract.ControllerAction.TERMINATE,
            message="Exiting session gracefully.",
        )

    dummy_router.connect("bye", bye_controller)

    prompt = presentation.PromptLoop(
        "test_cli",
        router=dummy_router,
        session=test_session,
    )

    prompt.run()

    assert "Exiting session gracefully." in dummy_view.messages


def test_prompt_unknown_route_writes_error_and_continues(
    dummy_router: testing.DummyRouter,
    test_session: contract.SessionContext,
    dummy_input_source: testing.DummyInputSource,
    dummy_view: testing.DummyView,
) -> None:
    """PromptLoop writes RouterError to view when route is unknown and continues processing next command."""

    dummy_input_source.feed_inputs("nonexistent_command", "exit")

    def exit_ctrl(
        session: contract.SessionContext,
        req: contract.IControllerRequest[contract.ControllerArguments],
    ) -> contract.ControllerResult:
        return contract.ControllerResult(action=contract.ControllerAction.TERMINATE)

    dummy_router.connect("exit", exit_ctrl)

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
