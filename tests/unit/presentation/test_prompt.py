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
        req: contract.ControllerRequest,
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
        req: contract.ControllerRequest,
    ) -> contract.ControllerResult:
        raise KeyboardInterrupt()

    def exit_controller(
        session: contract.SessionContext,
        req: contract.ControllerRequest,
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
        req: contract.ControllerRequest,
    ) -> contract.ControllerResult:
        raise exc

    def exit_controller(
        session: contract.SessionContext,
        req: contract.ControllerRequest,
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
        req: contract.ControllerRequest,
    ) -> contract.ControllerResult:
        return contract.ControllerResult(action=contract.ControllerAction.TERMINATE)

    dummy_router.connect("quit", quit_controller)

    runner.run(test_session, dummy_router)

    assert dummy_router.locate_calls == ["quit"]

