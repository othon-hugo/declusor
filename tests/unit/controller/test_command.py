"""Unit tests for CommandArguments and call_command in declusor.controller.command."""

from typing import is_typeddict

import pytest

from declusor import config, contract, testing
from declusor.controller import command as command_module


class TestCommandArguments:
    """Tests verifying CommandArguments TypedDict invariants and contract compliance."""

    def test_command_arguments__is_typeddict(self) -> None:
        """CommandArguments is a valid TypedDict type."""

        assert is_typeddict(command_module.CommandArguments)

    def test_command_arguments__declares_command_field(self) -> None:
        """CommandArguments specifies the command attribute as a string."""

        assert "command" in command_module.CommandArguments.__annotations__
        assert command_module.CommandArguments.__annotations__["command"] is str


class TestCommandController:
    """Tests verifying call_command execution, argument passing, and error propagation."""

    def test_call_command__valid_command_line__transmits_payload_and_returns_continue(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_profile: testing.DummyConnectionProfile,
        dummy_view: testing.DummyView,
    ) -> None:
        """call_command executes ExecuteCommand via session, transmits payload, and returns CONTINUE."""

        dummy_profile.set_rendered_command(config.OperationCode.EXEC_COMMAND, "rendered_whoami")
        req = testing.create_dummy_controller_request("whoami", command_module.CommandArguments)

        result = command_module.call_command(test_session, req)

        assert isinstance(result, contract.ControllerResult)
        assert result.action == contract.ControllerAction.CONTINUE
        assert dummy_connection.written == [b"rendered_whoami"]
        assert dummy_profile.render_calls == [(config.OperationCode.EXEC_COMMAND, ("whoami",))]
        assert dummy_view.binary_data == [b"chunk1\n", b"chunk2\n"]

    def test_call_command__command_with_flags_and_arguments__preserves_complete_string(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """call_command preserves complex command lines including flags, arguments, and quotes."""

        command_text = "grep -rn 'root' /etc/passwd"
        dummy_profile.set_rendered_command(config.OperationCode.EXEC_COMMAND, f"rendered_{command_text}")
        req = testing.create_dummy_controller_request(f'"{command_text}"', command_module.CommandArguments)

        result = command_module.call_command(test_session, req)

        assert result.action == contract.ControllerAction.CONTINUE
        assert dummy_profile.render_calls == [(config.OperationCode.EXEC_COMMAND, (command_text,))]
        assert dummy_connection.written == [f"rendered_{command_text}".encode()]

    def test_call_command__empty_request_line__raises_parser_error(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """call_command raises ParserError when the required command argument is omitted."""

        req = testing.create_dummy_controller_request("", command_module.CommandArguments)

        with pytest.raises(config.ParserError):
            command_module.call_command(test_session, req)

    def test_call_command__whitespace_only_request_line__raises_parser_error(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """call_command raises ParserError when request line consists solely of whitespace."""

        req = testing.create_dummy_controller_request("   \t  \n  ", command_module.CommandArguments)

        with pytest.raises(config.ParserError):
            command_module.call_command(test_session, req)

    def test_call_command__quoted_empty_command__raises_command_validation_error(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """call_command propagates CommandValidationError when parsed command line is blank."""

        req = testing.create_dummy_controller_request('""', command_module.CommandArguments)

        with pytest.raises(config.CommandValidationError) as exc_info:
            command_module.call_command(test_session, req)

        assert exc_info.value.field == "command_line"
        assert exc_info.value.value == ""
        assert isinstance(exc_info.value, config.InvalidOperation)

    def test_call_command__connection_write_failure__propagates_exception(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
    ) -> None:
        """call_command propagates connection exceptions to caller without swallowing them."""

        dummy_connection.write_error = config.ConnectionError("Transport socket failed")
        req = testing.create_dummy_controller_request("id", command_module.CommandArguments)

        with pytest.raises(config.ConnectionError, match="Transport socket failed"):
            command_module.call_command(test_session, req)

    def test_call_command__closed_connection__raises_connection_error(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
    ) -> None:
        """call_command propagates ConnectionError when executing over a closed connection."""

        dummy_connection.close()
        req = testing.create_dummy_controller_request("id", command_module.CommandArguments)

        with pytest.raises(config.ConnectionError, match="Connection is not open."):
            command_module.call_command(test_session, req)
