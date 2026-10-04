"""Unit tests for ExecuteArguments and call_execute in declusor.controller.execute."""

from pathlib import Path
from typing import is_typeddict

import pytest

from declusor import config, contract, testing, util
from declusor.controller import execute as execute_module


class TestExecuteArguments:
    """Tests verifying ExecuteArguments TypedDict invariants and contract compliance."""

    def test_execute_arguments__is_typeddict(self) -> None:
        """ExecuteArguments is a valid TypedDict type."""

        assert is_typeddict(execute_module.ExecuteArguments)

    def test_execute_arguments__declares_filepath_field(self) -> None:
        """ExecuteArguments specifies the filepath attribute as a string."""

        assert "filepath" in execute_module.ExecuteArguments.__annotations__
        assert execute_module.ExecuteArguments.__annotations__["filepath"] is str


class TestExecuteController:
    """Tests verifying call_execute local script reading, payload rendering, and execution."""

    def test_call_execute__valid_file__reads_encodes_and_executes_via_session(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_renderer: testing.DummyOperationRenderer,
        dummy_view: testing.DummyView,
    ) -> None:
        """call_execute reads script file, Base64 encodes content, renders payload, and returns CONTINUE."""

        script_file = tmp_path / "script.sh"
        script_file.write_text("echo 'hello from script'")
        expected_b64 = util.convert_to_base64(b"echo 'hello from script'")
        dummy_renderer.set_rendered_command(config.OperationCode.EXEC_FILE, "rendered_script_exec")
        req = testing.create_dummy_controller_request(str(script_file), execute_module.ExecuteArguments)

        result = execute_module.call_execute(test_session, req)

        assert isinstance(result, contract.ControllerResult)
        assert result.action == contract.ControllerAction.CONTINUE
        assert dummy_connection.written == [b"rendered_script_exec"]
        assert dummy_renderer.render_calls == [(config.OperationCode.EXEC_FILE, (expected_b64,))]
        assert dummy_view.binary_data == [b"chunk1\n", b"chunk2\n"]

    def test_call_execute__path_with_spaces__parses_and_executes_successfully(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_renderer: testing.DummyOperationRenderer,
    ) -> None:
        """call_execute correctly resolves quoted file paths containing whitespace characters."""

        spaced_dir = tmp_path / "my folder"
        spaced_dir.mkdir()
        script_file = spaced_dir / "target script.py"
        script_file.write_text("print('spaced path')")
        dummy_renderer.set_rendered_command(config.OperationCode.EXEC_FILE, "rendered_spaced")
        req = testing.create_dummy_controller_request(f'"{script_file}"', execute_module.ExecuteArguments)

        result = execute_module.call_execute(test_session, req)

        assert result.action == contract.ControllerAction.CONTINUE
        assert dummy_connection.written == [b"rendered_spaced"]

    def test_call_execute__empty_request_line__raises_parser_error(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """call_execute raises ParserError when the required filepath argument is omitted."""

        req = testing.create_dummy_controller_request("", execute_module.ExecuteArguments)

        with pytest.raises(config.ParserError):
            execute_module.call_execute(test_session, req)

    def test_call_execute__whitespace_only_request_line__raises_parser_error(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """call_execute raises ParserError when request line consists solely of whitespace."""

        req = testing.create_dummy_controller_request("   \t  \n  ", execute_module.ExecuteArguments)

        with pytest.raises(config.ParserError):
            execute_module.call_execute(test_session, req)

    def test_call_execute__nonexistent_file__raises_invalid_operation(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
    ) -> None:
        """call_execute raises InvalidOperation when local script file does not exist."""

        missing_file = tmp_path / "nonexistent_script_12345.sh"
        req = testing.create_dummy_controller_request(str(missing_file), execute_module.ExecuteArguments)

        with pytest.raises(config.InvalidOperation):
            execute_module.call_execute(test_session, req)

    def test_call_execute__directory_path__raises_invalid_operation(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
    ) -> None:
        """call_execute raises InvalidOperation when path targets a directory instead of a regular file."""

        target_dir = tmp_path / "script_dir"
        target_dir.mkdir()
        req = testing.create_dummy_controller_request(str(target_dir), execute_module.ExecuteArguments)

        with pytest.raises(config.InvalidOperation):
            execute_module.call_execute(test_session, req)

    def test_call_execute__connection_write_failure__propagates_exception(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
    ) -> None:
        """call_execute propagates connection write errors without swallowing them."""

        script_file = tmp_path / "exec.sh"
        script_file.write_text("echo test")
        dummy_connection.write_error = config.ConnectionError("Transport failure")
        req = testing.create_dummy_controller_request(str(script_file), execute_module.ExecuteArguments)

        with pytest.raises(config.ConnectionError, match="Transport failure"):
            execute_module.call_execute(test_session, req)
