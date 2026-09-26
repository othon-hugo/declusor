from pathlib import Path

from declusor import config, contract, controller, testing


def test_call_exit_returns_terminate_action(test_session: contract.SessionContext) -> None:
    """call_exit must return ControllerResult with action=TERMINATE."""

    req = testing.create_dummy_controller_request()
    result = controller.call_exit(test_session, req)

    assert isinstance(result, contract.ControllerResult)
    assert result.action == contract.ControllerAction.TERMINATE


def test_call_command_executes_with_dto_and_returns_continue(
    test_session: contract.SessionContext,
    dummy_connection: testing.DummyConnection,
) -> None:
    """call_command must construct ExecuteCommand with ExecuteCommandDTO and execute via session."""

    req = testing.create_dummy_controller_request("whoami")
    result = controller.call_command(test_session, req)

    assert dummy_connection.written == [b"whoami"]
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

    req = testing.create_dummy_controller_request(str(test_file))
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

    req = testing.create_dummy_controller_request(str(test_file))
    result = controller.call_upload(test_session, req)

    assert dummy_connection.written == [b"rendered_test_upload"]
    assert result.action == contract.ControllerAction.CONTINUE


def test_call_load_module_with_dto(
    test_session: contract.SessionContext,
    dummy_connection: testing.DummyConnection,
    dummy_file_store: testing.DummyPluginFileStore,
) -> None:
    """call_load must construct LoadModule with LoadModuleDTO and execute via session."""

    dummy_file_store.set_module("discovery/sysinfo", b"sysinfo_bytes")
    req = testing.create_dummy_controller_request("discovery/sysinfo")
    result = controller.call_load(test_session, req)

    assert dummy_file_store.load_module_calls == ["discovery/sysinfo"]
    assert dummy_connection.written == [b"sysinfo_bytes"]
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

    def cmd_a(session: contract.SessionContext, req: contract.ControllerRequest) -> contract.ControllerResult:
        """Command A usage."""

        return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)

    def cmd_longer(session: contract.SessionContext, req: contract.ControllerRequest) -> contract.ControllerResult:
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

    def cmd(session: contract.SessionContext, req: contract.ControllerRequest) -> contract.ControllerResult:
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

    def dynamic_cmd(session: contract.SessionContext, req: contract.ControllerRequest) -> contract.ControllerResult:
        """Dynamic command description."""

        return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)

    dummy_router.connect("dynamic", dynamic_cmd)
    req = testing.create_dummy_controller_request()

    result = help_ctrl(test_session, req)

    assert isinstance(result, contract.ControllerResult)
    assert result.action == contract.ControllerAction.CONTINUE
    assert dummy_view.messages == ["dynamic : Dynamic command description."]
