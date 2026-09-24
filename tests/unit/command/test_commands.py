from pathlib import Path

import pytest

from declusor import command, config, contract, testing


def test_execute_command_lifecycle(
    test_session: contract.SessionContext,
    dummy_connection: testing.DummyConnection,
    dummy_console: testing.DummyConsole,
) -> None:
    """ExecuteCommand transmits the raw command string and streams chunks to console."""

    dto = command.ExecuteCommandDTO(command_line="id")
    cmd = command.ExecuteCommand(dto=dto)

    test_session.execute(cmd)

    assert dummy_connection.written == [b"id"]
    assert dummy_console.binary_data == [b"chunk1\n", b"chunk2\n"]


def test_execute_file_lifecycle(
    tmp_path: Path,
    test_session: contract.SessionContext,
    dummy_connection: testing.DummyConnection,
    dummy_console: testing.DummyConsole,
    dummy_profile: testing.DummyConnectionProfile,
) -> None:
    """ExecuteFile encodes file content, invokes profile rendering, and executes."""

    script_file = tmp_path / "test.sh"
    script_file.write_text("echo hello")

    dummy_profile.set_rendered_command(config.OperationCode.EXEC_FILE, "rendered_exec_script")

    dto = command.ExecuteFileDTO(filepath=script_file)
    cmd = command.ExecuteFile(dto=dto)

    test_session.execute(cmd)

    assert len(dummy_profile.render_calls) == 1
    assert dummy_profile.render_calls[0][0] == config.OperationCode.EXEC_FILE
    assert dummy_connection.written == [b"rendered_exec_script"]
    assert len(dummy_console.binary_data) == 2


def test_upload_file_lifecycle(
    tmp_path: Path,
    test_session: contract.SessionContext,
    dummy_connection: testing.DummyConnection,
    dummy_console: testing.DummyConsole,
    dummy_profile: testing.DummyConnectionProfile,
) -> None:
    """UploadFile encodes file content, renders STORE_FILE command, and transmits."""

    data_file = tmp_path / "data.bin"
    data_file.write_bytes(b"content")

    dummy_profile.set_rendered_command(config.OperationCode.STORE_FILE, "rendered_upload_script")

    dto = command.UploadFileDTO(filepath=data_file)
    cmd = command.UploadFile(dto=dto)

    test_session.execute(cmd)

    assert len(dummy_profile.render_calls) == 1
    assert dummy_profile.render_calls[0][0] == config.OperationCode.STORE_FILE
    assert dummy_connection.written == [b"rendered_upload_script"]
    assert len(dummy_console.binary_data) == 2


def test_file_command_render_failure_raises(
    tmp_path: Path,
    test_session: contract.SessionContext,
    dummy_profile: testing.DummyConnectionProfile,
) -> None:
    """Commands raise InvalidOperation when profile cannot render operation command."""

    data_file = tmp_path / "fail.bin"
    data_file.write_bytes(b"content")

    dummy_profile.set_rendered_command(config.OperationCode.STORE_FILE, None)

    dto = command.UploadFileDTO(filepath=data_file)
    cmd = command.UploadFile(dto=dto)

    with pytest.raises(config.InvalidOperation, match="Failed to generate script data"):
        cmd.send_request(test_session)


def test_load_module_lifecycle(
    test_session: contract.SessionContext,
    dummy_connection: testing.DummyConnection,
    dummy_console: testing.DummyConsole,
    dummy_file_store: testing.DummyPluginFileStore,
) -> None:
    """LoadModule reads module bytes from file store and sends to remote client."""

    dummy_file_store.set_module("discovery/sysinfo", b"module_code_bytes")

    dto = command.LoadModuleDTO(module_name="discovery/sysinfo")
    cmd = command.LoadModule(dto=dto)

    test_session.execute(cmd)

    assert dummy_file_store.load_module_calls == ["discovery/sysinfo"]
    assert dummy_connection.written == [b"module_code_bytes"]
    assert len(dummy_console.binary_data) == 2


def test_load_module_missing_files_store(
    dummy_connection: testing.DummyConnection,
    dummy_console: testing.DummyConsole,
) -> None:
    """LoadModule raises CommandError if SessionContext has no file store configured."""

    session_no_files = contract.SessionContext(
        connection=dummy_connection,
        console=dummy_console,
        files=None,  # type: ignore[arg-type]
    )

    dto = command.LoadModuleDTO(module_name="discovery/sysinfo")
    cmd = command.LoadModule(dto=dto)

    with pytest.raises(config.CommandError, match="Client file store is not configured"):
        cmd.send_request(session_no_files)


def test_launch_shell_instantiation_with_dto() -> None:
    """LaunchShell stores DTO properly on instantiation."""

    dto = command.LaunchShellDTO(banner="Welcome to shell")
    cmd = command.LaunchShell(dto=dto)

    assert cmd.dto.banner == "Welcome to shell"
