from pathlib import Path
from unittest.mock import MagicMock, patch

from declusor import contract, controller


def test_call_exit_returns_terminate_action() -> None:
    """call_exit must return ControllerResult with action=TERMINATE."""

    deps = contract.ControllerDependencies(
        connection=MagicMock(spec=contract.IConnection),
        console=MagicMock(spec=contract.IConsole),
        files=MagicMock(spec=contract.IClientFileStore),
    )
    req = contract.ControllerRequest()

    result = controller.call_exit(deps, req)

    assert isinstance(result, contract.ControllerResult)
    assert result.action == contract.ControllerAction.TERMINATE


def test_call_command_executes_and_returns_continue() -> None:
    """call_command must instantiate ExecuteCommand with keyword arguments."""

    deps = contract.ControllerDependencies(
        connection=MagicMock(spec=contract.IConnection),
        console=MagicMock(spec=contract.IConsole),
        files=MagicMock(spec=contract.IClientFileStore),
    )
    req = contract.ControllerRequest("whoami")

    with patch("declusor.command.ExecuteCommand") as mock_command_cls:
        mock_instance = mock_command_cls.return_value
        result = controller.call_command(deps, req)

        mock_command_cls.assert_called_once_with(
            connection=deps.connection,
            console=deps.console,
            command_line="whoami",
        )
        mock_instance.execute.assert_called_once()
        assert result.action == contract.ControllerAction.CONTINUE


def test_call_shell_executes_and_returns_continue() -> None:
    """call_shell must execute LaunchShell with keyword arguments."""

    deps = contract.ControllerDependencies(
        connection=MagicMock(spec=contract.IConnection),
        console=MagicMock(spec=contract.IConsole),
        files=MagicMock(spec=contract.IClientFileStore),
    )
    req = contract.ControllerRequest()

    with patch("declusor.command.LaunchShell") as mock_shell_cls:
        mock_instance = mock_shell_cls.return_value
        result = controller.call_shell(deps, req)

        mock_shell_cls.assert_called_once_with(
            connection=deps.connection,
            console=deps.console,
        )
        mock_instance.execute.assert_called_once()
        assert result.action == contract.ControllerAction.CONTINUE
