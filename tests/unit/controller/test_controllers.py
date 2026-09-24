"""Unit tests for controller handlers using typed fixtures and test doubles."""

from pathlib import Path

from declusor import config, contract, controller
from declusor.testing import (
    DummyClientFileStore,
    DummyConnection,
    DummyConnectionProfile,
    DummyConsole,
    create_dummy_controller_request,
)


def test_call_exit_returns_terminate_action(test_session: contract.SessionContext) -> None:
    """call_exit must return ControllerResult with action=TERMINATE."""
    req = create_dummy_controller_request()
    result = controller.call_exit(test_session, req)

    assert isinstance(result, contract.ControllerResult)
    assert result.action == contract.ControllerAction.TERMINATE


def test_call_command_executes_with_dto_and_returns_continue(
    test_session: contract.SessionContext,
    dummy_connection: DummyConnection,
) -> None:
    """call_command must construct ExecuteCommand with ExecuteCommandDTO and execute via session."""
    req = create_dummy_controller_request("whoami")
    result = controller.call_command(test_session, req)

    assert dummy_connection.written == [b"whoami"]
    assert result.action == contract.ControllerAction.CONTINUE


def test_call_execute_file_with_dto(
    tmp_path: Path,
    test_session: contract.SessionContext,
    dummy_connection: DummyConnection,
    dummy_profile: DummyConnectionProfile,
) -> None:
    """call_execute must construct ExecuteFile with ExecuteFileDTO and execute via session."""
    test_file = tmp_path / "script.sh"
    test_file.write_text("echo test")
    dummy_profile.set_rendered_command(config.OperationCode.EXEC_FILE, "rendered_test_exec")

    req = create_dummy_controller_request(str(test_file))
    result = controller.call_execute(test_session, req)

    assert dummy_connection.written == [b"rendered_test_exec"]
    assert result.action == contract.ControllerAction.CONTINUE


def test_call_upload_file_with_dto(
    tmp_path: Path,
    test_session: contract.SessionContext,
    dummy_connection: DummyConnection,
    dummy_profile: DummyConnectionProfile,
) -> None:
    """call_upload must construct UploadFile with UploadFileDTO and execute via session."""
    test_file = tmp_path / "upload.bin"
    test_file.write_bytes(b"data")
    dummy_profile.set_rendered_command(config.OperationCode.STORE_FILE, "rendered_test_upload")

    req = create_dummy_controller_request(str(test_file))
    result = controller.call_upload(test_session, req)

    assert dummy_connection.written == [b"rendered_test_upload"]
    assert result.action == contract.ControllerAction.CONTINUE


def test_call_load_module_with_dto(
    test_session: contract.SessionContext,
    dummy_connection: DummyConnection,
    dummy_file_store: DummyClientFileStore,
) -> None:
    """call_load must construct LoadModule with LoadModuleDTO and execute via session."""
    dummy_file_store.set_module("discovery/sysinfo", b"sysinfo_bytes")
    req = create_dummy_controller_request("discovery/sysinfo")
    result = controller.call_load(test_session, req)

    assert dummy_file_store.load_module_calls == ["discovery/sysinfo"]
    assert dummy_connection.written == [b"sysinfo_bytes"]
    assert result.action == contract.ControllerAction.CONTINUE


def test_call_shell_executes_and_returns_continue(
    test_session: contract.SessionContext,
    dummy_console: DummyConsole,
) -> None:
    """call_shell must execute LaunchShell via session and return CONTINUE."""
    req = create_dummy_controller_request()
    dummy_console.input_exception = KeyboardInterrupt()

    result = controller.call_shell(test_session, req)

    assert result.action == contract.ControllerAction.CONTINUE
    assert "[keyboard interrupt received]" in dummy_console.messages
