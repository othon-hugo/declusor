import pytest

from declusor import config, contract, presentation, testing


def test_prompt_terminates_on_controller_terminate_action(
    dummy_router: testing.DummyRouter,
    dummy_connection: testing.DummyConnection,
    dummy_console: testing.DummyConsole,
    dummy_file_store: testing.DummyClientFileStore,
) -> None:
    """PromptCLI must stop cleanly when a controller signals ControllerAction.TERMINATE."""

    dummy_console.feed_inputs("exit")

    def exit_controller(
        session: contract.SessionContext,
        req: contract.ControllerRequest,
    ) -> contract.ControllerResult:
        return contract.ControllerResult(action=contract.ControllerAction.TERMINATE)

    dummy_router.connect("exit", exit_controller)

    prompt = presentation.PromptCLI(
        "test_cli",
        router=dummy_router,
        connection=dummy_connection,
        console=dummy_console,
        files=dummy_file_store,
    )

    prompt.run()

    assert dummy_router.locate_calls == ["exit"]


def test_prompt_init_missing_dependencies_raises(dummy_router: testing.DummyRouter) -> None:
    """Verify PromptCLI raises InvalidOperation when dependencies are incomplete."""

    with pytest.raises(config.InvalidOperation):
        presentation.PromptCLI("test_cli", router=dummy_router)


def test_prompt_handles_keyboard_interrupt_on_input(
    dummy_router: testing.DummyRouter,
    dummy_connection: testing.DummyConnection,
    dummy_console: testing.DummyConsole,
    dummy_file_store: testing.DummyClientFileStore,
) -> None:
    """PromptCLI must terminate loop gracefully on KeyboardInterrupt during input."""

    dummy_console.input_exception = KeyboardInterrupt()

    prompt = presentation.PromptCLI(
        "test_cli",
        router=dummy_router,
        connection=dummy_connection,
        console=dummy_console,
        files=dummy_file_store,
    )

    prompt.run()  # Must not raise


def test_prompt_handles_keyboard_interrupt_during_execution(
    dummy_router: testing.DummyRouter,
    dummy_connection: testing.DummyConnection,
    dummy_console: testing.DummyConsole,
    dummy_file_store: testing.DummyClientFileStore,
) -> None:
    """PromptCLI catches KeyboardInterrupt during command execution and continues."""

    dummy_console.feed_inputs("long_cmd", "exit")

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

    prompt = presentation.PromptCLI(
        "test_cli",
        router=dummy_router,
        connection=dummy_connection,
        console=dummy_console,
        files=dummy_file_store,
    )

    prompt.run()

    assert dummy_router.locate_calls == ["long_cmd", "exit"]


def test_prompt_handles_declusor_exception(
    dummy_router: testing.DummyRouter,
    dummy_connection: testing.DummyConnection,
    dummy_console: testing.DummyConsole,
    dummy_file_store: testing.DummyClientFileStore,
) -> None:
    """PromptCLI catches DeclusorException and prints error without terminating loop."""

    dummy_console.feed_inputs("fail_cmd", "exit")
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

    prompt = presentation.PromptCLI(
        "test_cli",
        router=dummy_router,
        connection=dummy_connection,
        console=dummy_console,
        files=dummy_file_store,
    )

    prompt.run()

    assert exc in dummy_console.errors
    assert dummy_router.locate_calls == ["fail_cmd", "exit"]
