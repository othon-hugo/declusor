from pathlib import Path
from unittest.mock import MagicMock, patch

from declusor import command, contract, controller


def test_call_exit_returns_terminate_action() -> None:
    """call_exit must return ControllerResult with action=TERMINATE."""
    session = contract.SessionContext(
        connection=MagicMock(spec=contract.IConnection),
        console=MagicMock(spec=contract.IConsole),
        files=MagicMock(spec=contract.IClientFileStore),
    )
    req = contract.ControllerRequest()

    result = controller.call_exit(session, req)

    assert isinstance(result, contract.ControllerResult)
    assert result.action == contract.ControllerAction.TERMINATE


def test_call_command_executes_with_dto_and_returns_continue() -> None:
    """call_command must construct ExecuteCommand with ExecuteCommandDTO and execute via session."""
    session = contract.SessionContext(
        connection=MagicMock(spec=contract.IConnection),
        console=MagicMock(spec=contract.IConsole),
        files=MagicMock(spec=contract.IClientFileStore),
    )
    req = contract.ControllerRequest("whoami")

    with patch("declusor.command.ExecuteCommand") as mock_command_cls:
        mock_instance = mock_command_cls.return_value
        result = controller.call_command(session, req)

        mock_command_cls.assert_called_once_with(command.ExecuteCommandDTO(command_line="whoami"))
        mock_instance.execute.assert_called_once_with(session)
        assert result.action == contract.ControllerAction.CONTINUE


def test_call_execute_file_with_dto(tmp_path: Path) -> None:
    """call_execute must construct ExecuteFile with ExecuteFileDTO and execute via session."""
    test_file = tmp_path / "script.sh"
    test_file.write_text("echo test")

    session = contract.SessionContext(
        connection=MagicMock(spec=contract.IConnection),
        console=MagicMock(spec=contract.IConsole),
        files=MagicMock(spec=contract.IClientFileStore),
    )
    req = contract.ControllerRequest(str(test_file))

    with patch("declusor.command.ExecuteFile") as mock_command_cls:
        mock_instance = mock_command_cls.return_value
        result = controller.call_execute(session, req)

        mock_command_cls.assert_called_once_with(command.ExecuteFileDTO(filepath=test_file))
        mock_instance.execute.assert_called_once_with(session)
        assert result.action == contract.ControllerAction.CONTINUE


def test_call_upload_file_with_dto(tmp_path: Path) -> None:
    """call_upload must construct UploadFile with UploadFileDTO and execute via session."""
    test_file = tmp_path / "upload.bin"
    test_file.write_bytes(b"data")

    session = contract.SessionContext(
        connection=MagicMock(spec=contract.IConnection),
        console=MagicMock(spec=contract.IConsole),
        files=MagicMock(spec=contract.IClientFileStore),
    )
    req = contract.ControllerRequest(str(test_file))

    with patch("declusor.command.UploadFile") as mock_command_cls:
        mock_instance = mock_command_cls.return_value
        result = controller.call_upload(session, req)

        mock_command_cls.assert_called_once_with(command.UploadFileDTO(filepath=test_file))
        mock_instance.execute.assert_called_once_with(session)
        assert result.action == contract.ControllerAction.CONTINUE


def test_call_load_module_with_dto() -> None:
    """call_load must construct LoadModule with LoadModuleDTO and execute via session."""
    session = contract.SessionContext(
        connection=MagicMock(spec=contract.IConnection),
        console=MagicMock(spec=contract.IConsole),
        files=MagicMock(spec=contract.IClientFileStore),
    )
    req = contract.ControllerRequest("discovery/sysinfo")

    with patch("declusor.command.LoadModule") as mock_command_cls:
        mock_instance = mock_command_cls.return_value
        result = controller.call_load(session, req)

        mock_command_cls.assert_called_once_with(command.LoadModuleDTO(module_name="discovery/sysinfo"))
        mock_instance.execute.assert_called_once_with(session)
        assert result.action == contract.ControllerAction.CONTINUE


def test_call_shell_executes_and_returns_continue() -> None:
    """call_shell must execute LaunchShell via session."""
    session = contract.SessionContext(
        connection=MagicMock(spec=contract.IConnection),
        console=MagicMock(spec=contract.IConsole),
        files=MagicMock(spec=contract.IClientFileStore),
    )
    req = contract.ControllerRequest()

    with patch("declusor.command.LaunchShell") as mock_shell_cls:
        mock_instance = mock_shell_cls.return_value
        result = controller.call_shell(session, req)

        mock_shell_cls.assert_called_once_with()
        mock_instance.execute.assert_called_once_with(session)
        assert result.action == contract.ControllerAction.CONTINUE
