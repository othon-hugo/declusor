from unittest.mock import MagicMock

import pytest

from declusor import config, contract
from declusor.presentation import PromptCLI


def test_prompt_terminates_on_controller_terminate_action() -> None:
    """PromptCLI must stop cleanly when a controller signals ControllerAction.TERMINATE."""
    mock_router = MagicMock(spec=contract.IRouter)
    mock_connection = MagicMock(spec=contract.IConnection)
    mock_console = MagicMock(spec=contract.IConsole)
    mock_files = MagicMock(spec=contract.IClientFileStore)

    mock_console.read_stripped_line.return_value = "exit"
    mock_controller = MagicMock(return_value=contract.ControllerResult(action=contract.ControllerAction.TERMINATE))
    mock_router.locate.return_value = mock_controller

    prompt = PromptCLI(
        "test_cli",
        router=mock_router,
        connection=mock_connection,
        console=mock_console,
        files=mock_files,
    )

    prompt.run()

    mock_router.locate.assert_called_once_with("exit")
    assert mock_controller.called


def test_prompt_init_missing_dependencies_raises() -> None:
    """Verify PromptCLI raises InvalidOperation when dependencies are incomplete."""
    mock_router = MagicMock(spec=contract.IRouter)

    with pytest.raises(config.InvalidOperation):
        PromptCLI("test_cli", router=mock_router)


def test_prompt_handles_keyboard_interrupt_on_input() -> None:
    """PromptCLI must terminate loop gracefully on KeyboardInterrupt during input."""
    mock_router = MagicMock(spec=contract.IRouter)
    mock_console = MagicMock(spec=contract.IConsole)
    mock_connection = MagicMock(spec=contract.IConnection)
    mock_files = MagicMock(spec=contract.IClientFileStore)

    mock_console.read_stripped_line.side_effect = KeyboardInterrupt

    prompt = PromptCLI(
        "test_cli",
        router=mock_router,
        connection=mock_connection,
        console=mock_console,
        files=mock_files,
    )

    prompt.run()  # Must not raise


def test_prompt_handles_keyboard_interrupt_during_execution() -> None:
    """PromptCLI catches KeyboardInterrupt during command execution and continues."""
    mock_router = MagicMock(spec=contract.IRouter)
    mock_console = MagicMock(spec=contract.IConsole)
    mock_connection = MagicMock(spec=contract.IConnection)
    mock_files = MagicMock(spec=contract.IClientFileStore)

    mock_console.read_stripped_line.side_effect = ["long_cmd", "exit"]
    mock_controller_interrupt = MagicMock(side_effect=KeyboardInterrupt)
    mock_controller_exit = MagicMock(return_value=contract.ControllerResult(action=contract.ControllerAction.TERMINATE))

    def locate_fn(route: str):
        if route == "long_cmd":
            return mock_controller_interrupt
        return mock_controller_exit

    mock_router.locate.side_effect = locate_fn

    prompt = PromptCLI(
        "test_cli",
        router=mock_router,
        connection=mock_connection,
        console=mock_console,
        files=mock_files,
    )

    prompt.run()
    assert mock_controller_interrupt.called
    assert mock_controller_exit.called


def test_prompt_handles_declusor_exception() -> None:
    """PromptCLI catches DeclusorException and prints error without terminating loop."""
    mock_router = MagicMock(spec=contract.IRouter)
    mock_console = MagicMock(spec=contract.IConsole)
    mock_connection = MagicMock(spec=contract.IConnection)
    mock_files = MagicMock(spec=contract.IClientFileStore)

    mock_console.read_stripped_line.side_effect = ["fail_cmd", "exit"]
    exc = config.CommandError("failed")
    mock_controller_fail = MagicMock(side_effect=exc)
    mock_controller_exit = MagicMock(return_value=contract.ControllerResult(action=contract.ControllerAction.TERMINATE))

    def locate_fn(route: str):
        if route == "fail_cmd":
            return mock_controller_fail
        return mock_controller_exit

    mock_router.locate.side_effect = locate_fn

    prompt = PromptCLI(
        "test_cli",
        router=mock_router,
        connection=mock_connection,
        console=mock_console,
        files=mock_files,
    )

    prompt.run()
    mock_console.write_error_message.assert_called_once_with(exc)
