from pathlib import Path

import pytest

from declusor import config, contract, controller, testing, util


def test_call_exit_returns_terminate_action(test_session: contract.SessionContext) -> None:
    """call_exit must return ControllerResult with action=TERMINATE."""

    req = testing.create_dummy_controller_request()
    result = controller.call_exit(test_session, req)

    assert isinstance(result, contract.ControllerResult)
    assert result.action == contract.ControllerAction.TERMINATE


def test_call_command_executes_with_dto_and_returns_continue(
    test_session: contract.SessionContext,
    dummy_connection: testing.DummyConnection,
    dummy_profile: testing.DummyConnectionProfile,
) -> None:
    """call_command must construct ExecuteCommand with ExecuteCommandDTO and execute via session."""

    dummy_profile.set_rendered_command(config.OperationCode.EXEC_COMMAND, "rendered_whoami")

    req = testing.create_dummy_controller_request("whoami", controller.CommandArguments)
    result = controller.call_command(test_session, req)

    assert dummy_connection.written == [b"rendered_whoami"]
    assert result.action == contract.ControllerAction.CONTINUE


def test_call_execute_file_with_dto(
    tmp_path: Path,
    test_session: contract.SessionContext,
    dummy_connection: testing.DummyConnection,
    dummy_profile: testing.DummyConnectionProfile,
) -> None:
    """call_execute must construct ExecuteFile with ExecuteFileDTO and execute via session."""

    test_file = tmp_path / "script.sh"
    test_file.write_text("echo test")
    dummy_profile.set_rendered_command(config.OperationCode.EXEC_FILE, "rendered_test_exec")

    req = testing.create_dummy_controller_request(str(test_file), controller.ExecuteArguments)
    result = controller.call_execute(test_session, req)

    assert dummy_connection.written == [b"rendered_test_exec"]
    assert result.action == contract.ControllerAction.CONTINUE


def test_call_upload_file_with_dto(
    tmp_path: Path,
    test_session: contract.SessionContext,
    dummy_connection: testing.DummyConnection,
    dummy_profile: testing.DummyConnectionProfile,
) -> None:
    """call_upload must construct UploadFile with UploadFileDTO and execute via session."""

    test_file = tmp_path / "upload.bin"
    test_file.write_bytes(b"data")
    dummy_profile.set_rendered_command(config.OperationCode.STORE_FILE, "rendered_test_upload")

    req = testing.create_dummy_controller_request(str(test_file), controller.UploadArguments)
    result = controller.call_upload(test_session, req)

    assert dummy_connection.written == [b"rendered_test_upload"]
    assert result.action == contract.ControllerAction.CONTINUE


def test_call_upload_file_with_destination(
    tmp_path: Path,
    test_session: contract.SessionContext,
    dummy_connection: testing.DummyConnection,
    dummy_profile: testing.DummyConnectionProfile,
) -> None:
    """call_upload must forward destination to UploadFileDTO when provided in request."""

    test_file = tmp_path / "upload.bin"
    test_file.write_bytes(b"data")
    dummy_profile.set_rendered_command(config.OperationCode.STORE_FILE, "rendered_dest_upload")

    req = testing.create_dummy_controller_request(f"{test_file} /tmp/dest.bin", controller.UploadArguments)
    result = controller.call_upload(test_session, req)

    assert dummy_connection.written == [b"rendered_dest_upload"]
    assert dummy_profile.render_calls[-1] == (config.OperationCode.STORE_FILE, (util.convert_to_base64(b"data"), "/tmp/dest.bin"))
    assert result.action == contract.ControllerAction.CONTINUE


def test_call_code_executes_with_dto_and_returns_continue(
    test_session: contract.SessionContext,
    dummy_connection: testing.DummyConnection,
    dummy_profile: testing.DummyConnectionProfile,
) -> None:
    """call_code must construct ExecuteCode with ExecuteCodeDTO and execute via session."""

    dummy_profile.set_rendered_command(config.OperationCode.EXEC_CODE, "rendered_code_call")

    req = testing.create_dummy_controller_request("print('hi')", controller.CodeArguments)
    result = controller.call_code(test_session, req)

    assert dummy_connection.written == [b"rendered_code_call"]
    assert result.action == contract.ControllerAction.CONTINUE


def test_call_load_module_with_dto(
    test_session: contract.SessionContext,
    dummy_connection: testing.DummyConnection,
    dummy_file_store: testing.DummyPluginFileStore,
    dummy_profile: testing.DummyConnectionProfile,
) -> None:
    """call_load must construct LoadModule with LoadModuleDTO and execute via session."""

    dummy_file_store.set_module("discovery/sysinfo", b"sysinfo_bytes")
    dummy_profile.set_rendered_command(config.OperationCode.LOAD_MODULE, "rendered_sysinfo_load")
    req = testing.create_dummy_controller_request("discovery/sysinfo", controller.LoadArguments)
    result = controller.call_load(test_session, req)

    assert dummy_file_store.load_module_calls == ["discovery/sysinfo"]
    assert dummy_connection.written == [b"rendered_sysinfo_load"]
    assert result.action == contract.ControllerAction.CONTINUE


def test_call_shell_executes_and_returns_continue(
    test_session: contract.SessionContext,
    dummy_view: testing.DummyView,
    dummy_input_source: testing.DummyInputSource,
) -> None:
    """call_shell must execute LaunchShell via session and return CONTINUE."""

    req = testing.create_dummy_controller_request()
    dummy_input_source.input_exception = KeyboardInterrupt()

    result = controller.call_shell(test_session, req)

    assert result.action == contract.ControllerAction.CONTINUE
    assert "[keyboard interrupt received]" in dummy_view.messages


def test_call_help_lists_all_routes_with_aligned_usage(
    test_session: contract.SessionContext,
    dummy_view: testing.DummyView,
    dummy_router: testing.DummyRouter,
) -> None:
    """call_help without arguments must list all routes aligned by key length."""

    def cmd_a(session: contract.SessionContext, req: contract.IControllerRequest[contract.ControllerArguments]) -> contract.ControllerResult:
        """Command A usage."""

        return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)

    def cmd_longer(session: contract.SessionContext, req: contract.IControllerRequest[contract.ControllerArguments]) -> contract.ControllerResult:
        """Command Longer usage."""

        return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)

    dummy_router.connect("alpha", cmd_a)
    dummy_router.connect("longer_cmd", cmd_longer)

    help_ctrl = controller.create_help_controller(dummy_router)
    req = testing.create_dummy_controller_request()

    result = help_ctrl(test_session, req)

    assert isinstance(result, contract.ControllerResult)
    assert result.action == contract.ControllerAction.CONTINUE
    assert dummy_view.messages == [
        "alpha      : Command A usage.",
        "longer_cmd : Command Longer usage.",
    ]


def test_call_help_with_specific_command(
    test_session: contract.SessionContext,
    dummy_view: testing.DummyView,
    dummy_router: testing.DummyRouter,
) -> None:
    """call_help with a specific command must display only that command's usage."""

    def cmd(session: contract.SessionContext, req: contract.IControllerRequest[contract.ControllerArguments]) -> contract.ControllerResult:
        """Specific command description."""

        return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)

    dummy_router.connect("target", cmd)

    help_ctrl = controller.create_help_controller(dummy_router)
    req = testing.create_dummy_controller_request("target")

    result = help_ctrl(test_session, req)

    assert isinstance(result, contract.ControllerResult)
    assert result.action == contract.ControllerAction.CONTINUE
    assert dummy_view.messages == ["target: Specific command description."]


def test_call_help_with_unknown_command_writes_error(
    test_session: contract.SessionContext,
    dummy_view: testing.DummyView,
    dummy_router: testing.DummyRouter,
) -> None:
    """call_help with an unknown command must write an error to the view."""

    help_ctrl = controller.create_help_controller(dummy_router)
    req = testing.create_dummy_controller_request("unknown_cmd")

    result = help_ctrl(test_session, req)

    assert isinstance(result, contract.ControllerResult)
    assert result.action == contract.ControllerAction.CONTINUE
    assert len(dummy_view.errors) == 1
    assert "Unknown command: 'unknown_cmd'" in str(dummy_view.errors[0])


def test_call_help_empty_router_writes_notice(
    test_session: contract.SessionContext,
    dummy_view: testing.DummyView,
    dummy_router: testing.DummyRouter,
) -> None:
    """call_help on empty router must display no commands available."""

    help_ctrl = controller.create_help_controller(dummy_router)
    req = testing.create_dummy_controller_request()

    result = help_ctrl(test_session, req)

    assert isinstance(result, contract.ControllerResult)
    assert result.action == contract.ControllerAction.CONTINUE
    assert dummy_view.messages == ["No commands available."]


def test_call_help_reflects_dynamically_added_routes(
    test_session: contract.SessionContext,
    dummy_view: testing.DummyView,
    dummy_router: testing.DummyRouter,
) -> None:
    """call_help must query router dynamically, reflecting routes connected after creation."""

    help_ctrl = controller.create_help_controller(dummy_router)

    def dynamic_cmd(session: contract.SessionContext, req: contract.IControllerRequest[contract.ControllerArguments]) -> contract.ControllerResult:
        """Dynamic command description."""

        return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)

    dummy_router.connect("dynamic", dynamic_cmd)
    req = testing.create_dummy_controller_request()

    result = help_ctrl(test_session, req)

    assert isinstance(result, contract.ControllerResult)
    assert result.action == contract.ControllerAction.CONTINUE
    assert dummy_view.messages == ["dynamic : Dynamic command description."]


def test_call_command_empty_request_raises_parser_error(test_session: contract.SessionContext) -> None:
    """call_command raises ParserError when required command argument is omitted."""

    req = testing.create_dummy_controller_request("", controller.CommandArguments)
    with pytest.raises(config.ParserError):
        controller.call_command(test_session, req)


def test_call_execute_empty_request_raises_parser_error(test_session: contract.SessionContext) -> None:
    """call_execute raises ParserError when required filepath argument is omitted."""

    req = testing.create_dummy_controller_request("", controller.ExecuteArguments)
    with pytest.raises(config.ParserError):
        controller.call_execute(test_session, req)


def test_call_execute_nonexistent_file_raises_invalid_operation(test_session: contract.SessionContext) -> None:
    """call_execute raises InvalidOperation when script file does not exist."""

    req = testing.create_dummy_controller_request("/tmp/nonexistent_script_987654.sh", controller.ExecuteArguments)
    with pytest.raises(config.InvalidOperation):
        controller.call_execute(test_session, req)


def test_call_upload_empty_request_raises_parser_error(test_session: contract.SessionContext) -> None:
    """call_upload raises ParserError when required filepath argument is omitted."""

    req = testing.create_dummy_controller_request("", controller.UploadArguments)
    with pytest.raises(config.ParserError):
        controller.call_upload(test_session, req)


def test_call_upload_nonexistent_file_raises_invalid_operation(test_session: contract.SessionContext) -> None:
    """call_upload raises InvalidOperation when upload source file does not exist."""

    req = testing.create_dummy_controller_request("/tmp/nonexistent_upload_987654.bin", controller.UploadArguments)
    with pytest.raises(config.InvalidOperation):
        controller.call_upload(test_session, req)


def test_call_code_empty_request_raises_parser_error(test_session: contract.SessionContext) -> None:
    """call_code raises ParserError when required code argument is omitted."""

    req = testing.create_dummy_controller_request("", controller.CodeArguments)
    with pytest.raises(config.ParserError):
        controller.call_code(test_session, req)


def test_call_load_empty_request_raises_parser_error(test_session: contract.SessionContext) -> None:
    """call_load raises ParserError when required module argument is omitted."""

    req = testing.create_dummy_controller_request("", controller.LoadArguments)
    with pytest.raises(config.ParserError):
        controller.call_load(test_session, req)


def test_call_load_missing_module_raises_invalid_operation(
    test_session: contract.SessionContext,
    dummy_file_store: testing.DummyPluginFileStore,
) -> None:
    """call_load raises InvalidOperation when requested module cannot be loaded by the store."""

    dummy_file_store.load_module_error = config.InvalidOperation("Module missing")
    req = testing.create_dummy_controller_request("discovery/missing_module", controller.LoadArguments)
    with pytest.raises(config.InvalidOperation, match="Module missing"):
        controller.call_load(test_session, req)
