"""Unit tests for ShellArguments and call_shell in declusor.controller.shell."""

from typing import is_typeddict

import pytest

from declusor import config, contract, testing
from declusor.controller import shell as shell_module


class ScriptedInputSource(testing.DummyInputSource):
    """Input source that yields queued lines and raises KeyboardInterrupt when exhausted."""

    def read_raw(self, prompt: str = "", /) -> str:
        self.prompts.append(prompt)

        if self.input_exception is not None:
            exc = self.input_exception
            self.input_exception = None
            raise exc

        if not self._inputs:
            raise KeyboardInterrupt()

        line = self._inputs.pop(0)
        return line if line.endswith("\n") else f"{line}\n"


class TestShellArguments:
    """Tests verifying ShellArguments TypedDict invariants and contract compliance."""

    def test_shell_arguments__is_typeddict(self) -> None:
        """ShellArguments is a valid TypedDict type."""

        assert is_typeddict(shell_module.ShellArguments)

    def test_shell_arguments__total_is_false(self) -> None:
        """ShellArguments declares total=False allowing empty argument mappings."""

        assert shell_module.ShellArguments.__total__ is False

    def test_shell_arguments__accepts_empty_mapping(self) -> None:
        """An empty mapping satisfies ShellArguments."""

        empty_args: shell_module.ShellArguments = {}

        assert isinstance(empty_args, dict)
        assert len(empty_args) == 0


class TestShellController:
    """Tests verifying call_shell execution, keyboard interrupt resilience, and session forwarding."""

    def test_call_shell__standard_invocation__executes_shell_command_and_returns_continue(
        self,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """call_shell executes LaunchShell and returns CONTINUE on interactive session conclusion."""

        dummy_input_source.input_exception = KeyboardInterrupt()
        req = testing.create_dummy_controller_request("", shell_module.ShellArguments)

        result = shell_module.call_shell(test_session, req)

        assert isinstance(result, contract.ControllerResult)
        assert result.action == contract.ControllerAction.CONTINUE

    def test_call_shell__keyboard_interrupt__displays_notice_and_returns_continue(
        self,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
        dummy_view: testing.DummyView,
    ) -> None:
        """call_shell traps KeyboardInterrupt, displays interrupt notice, and resumes prompt loop."""

        dummy_input_source.input_exception = KeyboardInterrupt()
        req = testing.create_dummy_controller_request("", shell_module.ShellArguments)

        result = shell_module.call_shell(test_session, req)

        assert result.action == contract.ControllerAction.CONTINUE
        assert "[keyboard interrupt received]" in dummy_view.messages

    def test_call_shell__interactive_input__transmits_rendered_commands_over_connection(
        self,
        dummy_connection: testing.DummyConnection,
        dummy_profile: testing.DummyConnectionProfile,
        dummy_view: testing.DummyView,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """call_shell forwards typed operator commands to connection before keyboard interrupt."""

        dummy_profile.set_rendered_command(config.OperationCode.EXEC_COMMAND, "rendered_interactive_cmd")
        scripted_input = ScriptedInputSource(["pwd"])
        session = contract.SessionContext(
            connection=dummy_connection,
            view=dummy_view,
            input_source=scripted_input,
            plugin_processor=dummy_file_store,
        )
        req = testing.create_dummy_controller_request("", shell_module.ShellArguments)

        result = shell_module.call_shell(session, req)

        assert result.action == contract.ControllerAction.CONTINUE
        assert dummy_connection.written == [b"rendered_interactive_cmd"]
        assert dummy_profile.render_calls == [(config.OperationCode.EXEC_COMMAND, ("pwd\n",))]

    def test_call_shell__missing_input_source__raises_invalid_operation(
        self,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """call_shell raises InvalidOperation when session does not provide an input source."""

        session_without_input = contract.SessionContext(
            connection=dummy_connection,
            view=dummy_view,
            input_source=None,
            plugin_processor=dummy_file_store,
        )
        req = testing.create_dummy_controller_request("", shell_module.ShellArguments)

        with pytest.raises(config.InvalidOperation, match="requires an active input source"):
            shell_module.call_shell(session_without_input, req)

    def test_call_shell__extraneous_request_tokens__ignores_arguments(
        self,
        test_session: contract.SessionContext,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """call_shell ignores arbitrary request tokens passed on the command line."""

        dummy_input_source.input_exception = KeyboardInterrupt()
        req = testing.create_dummy_controller_request("--verbose --color=always", shell_module.ShellArguments)

        result = shell_module.call_shell(test_session, req)

        assert result.action == contract.ControllerAction.CONTINUE
