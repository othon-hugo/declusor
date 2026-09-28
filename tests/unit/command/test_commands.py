from pathlib import Path

import pytest

from declusor import command, config, contract, testing


def test_execute_command_lifecycle(
    test_session: contract.SessionContext,
    dummy_connection: testing.DummyConnection,
    dummy_view: testing.DummyView,
    dummy_profile: testing.DummyConnectionProfile,
) -> None:
    """ExecuteCommand transmits the rendered command string and streams chunks to view."""

    dummy_profile.set_rendered_command(config.OperationCode.EXEC_COMMAND, "rendered_id")

    dto = command.ExecuteCommandDTO(command_line="id")
    cmd = command.ExecuteCommand(dto)

    test_session.execute(cmd)

    assert len(dummy_profile.render_calls) == 1
    assert dummy_profile.render_calls[0] == (config.OperationCode.EXEC_COMMAND, ("id",))
    assert dummy_connection.written == [b"rendered_id"]
    assert dummy_view.binary_data == [b"chunk1\n", b"chunk2\n"]


def test_execute_command_lifecycle_fallback_unrendered(
    test_session: contract.SessionContext,
    dummy_connection: testing.DummyConnection,
    dummy_view: testing.DummyView,
    dummy_profile: testing.DummyConnectionProfile,
) -> None:
    """ExecuteCommand transmits raw command bytes when profile returns None."""

    dummy_profile.set_rendered_command(config.OperationCode.EXEC_COMMAND, None)

    dto = command.ExecuteCommandDTO(command_line="id")
    cmd = command.ExecuteCommand(dto)

    test_session.execute(cmd)

    assert len(dummy_profile.render_calls) == 1
    assert dummy_profile.render_calls[0] == (config.OperationCode.EXEC_COMMAND, ("id",))
    assert dummy_connection.written == [b"id"]
    assert dummy_view.binary_data == [b"chunk1\n", b"chunk2\n"]


def test_execute_code_lifecycle(
    test_session: contract.SessionContext,
    dummy_connection: testing.DummyConnection,
    dummy_view: testing.DummyView,
    dummy_profile: testing.DummyConnectionProfile,
) -> None:
    """ExecuteCode transmits the rendered code string and streams chunks to view."""

    dummy_profile.set_rendered_command(config.OperationCode.EXEC_CODE, "rendered_code")

    dto = command.ExecuteCodeDTO(code="print('hello')")
    cmd = command.ExecuteCode(dto)

    test_session.execute(cmd)

    assert len(dummy_profile.render_calls) == 1
    assert dummy_profile.render_calls[0] == (config.OperationCode.EXEC_CODE, ("print('hello')",))
    assert dummy_connection.written == [b"rendered_code"]
    assert dummy_view.binary_data == [b"chunk1\n", b"chunk2\n"]


def test_execute_code_lifecycle_fallback_unrendered(
    test_session: contract.SessionContext,
    dummy_connection: testing.DummyConnection,
    dummy_view: testing.DummyView,
    dummy_profile: testing.DummyConnectionProfile,
) -> None:
    """ExecuteCode transmits raw code bytes when profile returns None."""

    dummy_profile.set_rendered_command(config.OperationCode.EXEC_CODE, None)

    dto = command.ExecuteCodeDTO(code="print('hello')")
    cmd = command.ExecuteCode(dto)

    test_session.execute(cmd)

    assert len(dummy_profile.render_calls) == 1
    assert dummy_profile.render_calls[0] == (config.OperationCode.EXEC_CODE, ("print('hello')",))
    assert dummy_connection.written == [b"print('hello')"]
    assert dummy_view.binary_data == [b"chunk1\n", b"chunk2\n"]


def test_execute_file_lifecycle(
    tmp_path: Path,
    test_session: contract.SessionContext,
    dummy_connection: testing.DummyConnection,
    dummy_view: testing.DummyView,
    dummy_profile: testing.DummyConnectionProfile,
) -> None:
    """ExecuteFile encodes file content, invokes profile rendering, and executes."""

    script_file = tmp_path / "test.sh"
    script_file.write_text("echo hello")

    dummy_profile.set_rendered_command(config.OperationCode.EXEC_FILE, "rendered_exec_script")

    dto = command.ExecuteFileDTO(filepath=script_file)
    cmd = command.ExecuteFile(dto)

    test_session.execute(cmd)

    assert len(dummy_profile.render_calls) == 1
    assert dummy_profile.render_calls[0][0] == config.OperationCode.EXEC_FILE
    assert dummy_connection.written == [b"rendered_exec_script"]
    assert len(dummy_view.binary_data) == 2


def test_upload_file_lifecycle(
    tmp_path: Path,
    test_session: contract.SessionContext,
    dummy_connection: testing.DummyConnection,
    dummy_view: testing.DummyView,
    dummy_profile: testing.DummyConnectionProfile,
) -> None:
    """UploadFile encodes file content, renders STORE_FILE command, and transmits."""

    data_file = tmp_path / "data.bin"
    data_file.write_bytes(b"content")

    dummy_profile.set_rendered_command(config.OperationCode.STORE_FILE, "rendered_upload_script")

    dto = command.UploadFileDTO(filepath=data_file)
    cmd = command.UploadFile(dto)

    test_session.execute(cmd)

    assert len(dummy_profile.render_calls) == 1
    assert dummy_profile.render_calls[0][0] == config.OperationCode.STORE_FILE
    assert dummy_connection.written == [b"rendered_upload_script"]
    assert len(dummy_view.binary_data) == 2


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
    cmd = command.UploadFile(dto)

    with pytest.raises(config.InvalidOperation, match="Failed to generate script data"):
        cmd.send_request(test_session)


def test_load_module_lifecycle(
    test_session: contract.SessionContext,
    dummy_connection: testing.DummyConnection,
    dummy_view: testing.DummyView,
    dummy_file_store: testing.DummyPluginFileStore,
    dummy_profile: testing.DummyConnectionProfile,
) -> None:
    """LoadModule reads module bytes, renders LOAD_MODULE opcode, and sends to remote client."""

    dummy_file_store.set_module("discovery/sysinfo", b"module_code_bytes")
    dummy_profile.set_rendered_command(config.OperationCode.LOAD_MODULE, "rendered_module_load")

    dto = command.LoadModuleDTO(module_name="discovery/sysinfo")
    cmd = command.LoadModule(dto)

    test_session.execute(cmd)

    assert dummy_file_store.load_module_calls == ["discovery/sysinfo"]
    assert len(dummy_profile.render_calls) == 1
    assert dummy_profile.render_calls[0][0] == config.OperationCode.LOAD_MODULE
    assert dummy_connection.written == [b"rendered_module_load"]
    assert len(dummy_view.binary_data) == 2


def test_load_module_render_failure_raises(
    test_session: contract.SessionContext,
    dummy_file_store: testing.DummyPluginFileStore,
    dummy_profile: testing.DummyConnectionProfile,
) -> None:
    """LoadModule raises InvalidOperation when profile cannot render LOAD_MODULE command."""

    dummy_file_store.set_module("discovery/sysinfo", b"module_code_bytes")
    dummy_profile.set_rendered_command(config.OperationCode.LOAD_MODULE, None)

    dto = command.LoadModuleDTO(module_name="discovery/sysinfo")
    cmd = command.LoadModule(dto)

    with pytest.raises(config.InvalidOperation, match="Failed to generate script data for module loading"):
        cmd.send_request(test_session)


def test_load_module_missing_files_store(
    dummy_connection: testing.DummyConnection,
    dummy_view: testing.DummyView,
    dummy_input_source: testing.DummyInputSource,
) -> None:
    """LoadModule raises CommandError if SessionContext has no file store configured."""

    session_no_files = contract.SessionContext(
        connection=dummy_connection,
        view=dummy_view,
        input_source=dummy_input_source,
        plugin_processor=None,  # type: ignore[arg-type]
    )

    dto = command.LoadModuleDTO(module_name="discovery/sysinfo")
    cmd = command.LoadModule(dto)

    with pytest.raises(config.CommandError, match="Client file store is not configured"):
        cmd.send_request(session_no_files)


def test_launch_shell_instantiation_with_dto() -> None:
    """LaunchShell stores DTO properly on instantiation."""

    dto = command.LaunchShellDTO(banner="Welcome to shell")
    cmd = command.LaunchShell(dto)

    assert cmd._dto.banner == "Welcome to shell"
