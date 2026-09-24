from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from declusor import command, config, contract


@pytest.fixture
def session() -> contract.SessionContext:
    connection = MagicMock(spec=contract.IConnection)
    connection.read.return_value = [b"chunk1\n", b"chunk2\n"]
    console = MagicMock(spec=contract.IConsole)
    files = MagicMock(spec=contract.IClientFileStore)

    return contract.SessionContext(
        connection=connection,
        console=console,
        files=files,
    )


def test_execute_command_lifecycle(session: contract.SessionContext) -> None:
    dto = command.ExecuteCommandDTO(command_line="id")
    cmd = command.ExecuteCommand(dto=dto)

    session.execute(cmd)

    session.connection.write.assert_called_once_with(b"id")
    assert session.console.write_binary_data.call_args_list == [
        call(b"chunk1\n"),
        call(b"chunk2\n"),
    ]


def test_execute_file_lifecycle(tmp_path: Path, session: contract.SessionContext) -> None:
    script_file = tmp_path / "test.sh"
    script_file.write_text("echo hello")

    session.connection.client.render_operation_command.return_value = "rendered_exec_script"

    dto = command.ExecuteFileDTO(filepath=script_file)
    cmd = command.(dto=dto)

    session.execute(cmd)

    session.connection.client.render_operation_command.assert_called_once()
    session.connection.write.assert_called_once_with(b"rendered_exec_script")
    assert session.console.write_binary_data.call_count == 2


def test_upload_file_lifecycle(tmp_path: Path, session: contract.SessionContext) -> None:
    data_file = tmp_path / "data.bin"
    data_file.write_bytes(b"content")

    session.connection.client.render_operation_command.return_value = "rendered_upload_script"

    dto = command.UploadFileDTO(filepath=data_file)
    cmd = command.UploadFile(dto=dto)

    session.execute(cmd)

    session.connection.client.render_operation_command.assert_called_once()
    session.connection.write.assert_called_once_with(b"rendered_upload_script")
    assert session.console.write_binary_data.call_count == 2


def test_file_command_render_failure_raises(tmp_path: Path, session: contract.SessionContext) -> None:
    data_file = tmp_path / "fail.bin"
    data_file.write_bytes(b"content")

    session.connection.client.render_operation_command.return_value = None

    dto = command.UploadFileDTO(filepath=data_file)
    cmd = command.UploadFile(dto=dto)

    with pytest.raises(config.InvalidOperation, match="Failed to generate script data"):
        cmd.send_request(session)


def test_load_module_lifecycle(session: contract.SessionContext) -> None:
    session.files.load_module.return_value = b"module_code_bytes"

    dto = command.LoadModuleDTO(module_name="discovery/sysinfo")
    cmd = command.LoadModule(dto=dto)

    session.execute(cmd)

    session.files.load_module.assert_called_once_with("discovery/sysinfo")
    session.connection.write.assert_called_once_with(b"module_code_bytes")
    assert session.console.write_binary_data.call_count == 2


def test_load_module_missing_files_store() -> None:
    session_no_files = contract.SessionContext(
        connection=MagicMock(spec=contract.IConnection),
        console=MagicMock(spec=contract.IConsole),
        files=None,  # type: ignore[arg-type]
    )

    dto = command.LoadModuleDTO(module_name="discovery/sysinfo")
    cmd = command.LoadModule(dto=dto)

    with pytest.raises(config.CommandError, match="Client file store is not configured"):
        cmd.send_request(session_no_files)


def test_launch_shell_instantiation_with_dto() -> None:
    dto = command.LaunchShellDTO(banner="Welcome to shell")
    cmd = command.LaunchShell(dto=dto)

    assert cmd.dto.banner == "Welcome to shell"
