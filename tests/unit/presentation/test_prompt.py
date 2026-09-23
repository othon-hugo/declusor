from unittest.mock import MagicMock

from declusor import contract
from declusor.presentation import PromptCLI


def test_prompt_terminates_on_controller_terminate_action() -> None:
    """PromptCLI must stop cleanly when a controller signals ControllerAction.TERMINATE."""

    mock_router = MagicMock(spec=contract.IRouter)
    mock_connection = MagicMock(spec=contract.IConnection)
    mock_console = MagicMock(spec=contract.IConsole)
    mock_files = MagicMock(spec=contract.IClientFileStore)

    # User enters "exit"
    mock_console.read_stripped_line.return_value = "exit"

    # Route maps "exit" to controller returning ControllerResult(action=TERMINATE)
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
