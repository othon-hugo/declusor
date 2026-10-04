"""Unit tests for CodeArguments and call_code in declusor.controller.code."""

from typing import is_typeddict

import pytest

from declusor import config, contract, testing
from declusor.controller import code as code_module


class TestCodeArguments:
    """Tests verifying CodeArguments TypedDict invariants and contract compliance."""

    def test_code_arguments__is_typeddict(self) -> None:
        """CodeArguments is a valid TypedDict type."""

        assert is_typeddict(code_module.CodeArguments)

    def test_code_arguments__declares_code_field(self) -> None:
        """CodeArguments specifies the code attribute as a string."""

        assert "code" in code_module.CodeArguments.__annotations__
        assert code_module.CodeArguments.__annotations__["code"] is str


class TestCodeController:
    """Tests verifying call_code execution, code snippet forwarding, and error propagation."""

    def test_call_code__valid_snippet__transmits_payload_and_returns_continue(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_renderer: testing.DummyOperationRenderer,
        dummy_view: testing.DummyView,
    ) -> None:
        """call_code executes ExecuteCode via session, transmits payload, and returns CONTINUE."""

        snippet = "import sys; print(sys.version)"
        dummy_renderer.set_rendered_command(config.OperationCode.EXEC_CODE, "rendered_sys_version")
        req = testing.create_dummy_controller_request(f'"{snippet}"', code_module.CodeArguments)

        result = code_module.call_code(test_session, req)

        assert isinstance(result, contract.ControllerResult)
        assert result.action == contract.ControllerAction.CONTINUE
        assert dummy_connection.written == [b"rendered_sys_version"]
        assert dummy_renderer.render_calls == [(config.OperationCode.EXEC_CODE, (snippet,))]
        assert dummy_view.binary_data == [b"chunk1\n", b"chunk2\n"]

    def test_call_code__complex_multiline_snippet__preserves_complete_code(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_renderer: testing.DummyOperationRenderer,
    ) -> None:
        """call_code preserves multiline code blocks and inner quotation."""

        snippet = "def greet(name):\n    return f'hello {name}'\nprint(greet('declusor'))"
        dummy_renderer.set_rendered_command(config.OperationCode.EXEC_CODE, "rendered_greet")
        req = testing.create_dummy_controller_request(f'"{snippet}"', code_module.CodeArguments)

        result = code_module.call_code(test_session, req)

        assert result.action == contract.ControllerAction.CONTINUE
        assert dummy_renderer.render_calls == [(config.OperationCode.EXEC_CODE, (snippet,))]
        assert dummy_connection.written == [b"rendered_greet"]

    def test_call_code__empty_request_line__raises_parser_error(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """call_code raises ParserError when the required code argument is omitted."""

        req = testing.create_dummy_controller_request("", code_module.CodeArguments)

        with pytest.raises(config.ParserError):
            code_module.call_code(test_session, req)

    def test_call_code__whitespace_only_request_line__raises_parser_error(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """call_code raises ParserError when request line consists solely of whitespace."""

        req = testing.create_dummy_controller_request("   \t  \n  ", code_module.CodeArguments)

        with pytest.raises(config.ParserError):
            code_module.call_code(test_session, req)

    def test_call_code__quoted_empty_code__raises_command_validation_error(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """call_code propagates CommandValidationError when parsed code string is blank."""

        req = testing.create_dummy_controller_request('""', code_module.CodeArguments)

        with pytest.raises(config.CommandValidationError) as exc_info:
            code_module.call_code(test_session, req)

        assert exc_info.value.field == "code"
        assert exc_info.value.value == ""
        assert isinstance(exc_info.value, config.InvalidOperation)

    def test_call_code__connection_write_failure__propagates_exception(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
    ) -> None:
        """call_code propagates transport write failures without swallowing them."""

        dummy_connection.write_error = config.ConnectionError("Code socket transport error")
        req = testing.create_dummy_controller_request('"1 + 1"', code_module.CodeArguments)

        with pytest.raises(config.ConnectionError, match="Code socket transport error"):
            code_module.call_code(test_session, req)

    def test_call_code__closed_connection__raises_connection_error(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
    ) -> None:
        """call_code propagates ConnectionError when executing over a closed connection."""

        dummy_connection.close()
        req = testing.create_dummy_controller_request('"1 + 1"', code_module.CodeArguments)

        with pytest.raises(config.ConnectionError, match="Connection is closed."):
            code_module.call_code(test_session, req)
