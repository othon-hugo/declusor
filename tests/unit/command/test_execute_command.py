"""Unit tests for ExecuteCommandDTO and ExecuteCommand in declusor.command."""

from dataclasses import FrozenInstanceError

import pytest

from declusor import config, contract, testing
from declusor.command.execute_command import ExecuteCommand, ExecuteCommandDTO


class TestExecuteCommandDTO:
    """Tests verifying ExecuteCommandDTO validation, immutability, and equality invariants."""

    @pytest.mark.parametrize(
        "valid_command",
        [
            "uname -a",
            "id",
            "ls -la",
            "cat /etc/os-release",
            "echo 'hello world'",
        ],
    )
    def test_execute_command_dto_init__valid_command_line__preserves_command_line(
        self,
        valid_command: str,
    ) -> None:
        """ExecuteCommandDTO accepts valid non-empty command line strings without alteration."""

        dto = ExecuteCommandDTO(command_line=valid_command)

        assert dto.command_line == valid_command

    @pytest.mark.parametrize(
        "invalid_command",
        [
            "",
            " ",
            "\t",
            "\n",
            "\t\n",
            "\r\n",
            "   \t   \r\n   ",
        ],
    )
    def test_execute_command_dto_init__empty_or_whitespace__raises_command_validation_error(
        self,
        invalid_command: str,
    ) -> None:
        """ExecuteCommandDTO rejects empty or whitespace-only strings with CommandValidationError."""

        with pytest.raises(config.CommandValidationError) as exc_info:
            ExecuteCommandDTO(command_line=invalid_command)

        assert exc_info.value.field == "command_line"
        assert exc_info.value.value == invalid_command
        assert isinstance(exc_info.value, config.InvalidOperation)
        assert isinstance(exc_info.value, config.CommandError)
        assert "Command line cannot be empty." in str(exc_info.value)

    def test_execute_command_dto_immutability__reassign_attribute__raises_frozen_instance_error(self) -> None:
        """ExecuteCommandDTO is frozen and raises FrozenInstanceError on attribute reassignment."""

        dto = ExecuteCommandDTO(command_line="uname -a")

        with pytest.raises(FrozenInstanceError):
            dto.command_line = "id"  # type: ignore[misc]

    def test_execute_command_dto_equality__identical_commands__evaluates_equal(self) -> None:
        """ExecuteCommandDTO instances with identical command lines compare equal."""

        dto_first = ExecuteCommandDTO(command_line="id")
        dto_second = ExecuteCommandDTO(command_line="id")

        assert dto_first == dto_second
        assert hash(dto_first) == hash(dto_second)


class TestExecuteCommand:
    """Tests verifying ExecuteCommand request transmission, renderer fallbacks, and streaming."""

    def test_execute_command_send_request__successful_render__transmits_rendered_payload(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """ExecuteCommand invokes renderer with EXEC_COMMAND opcode and transmits rendered payload."""

        command_line = "uname -a"
        rendered_payload = "rendered_uname_command"
        dummy_profile.set_rendered_command(config.OperationCode.EXEC_COMMAND, rendered_payload)

        dto = ExecuteCommandDTO(command_line=command_line)
        command = ExecuteCommand(dto)

        command.send_request(test_session)

        assert dummy_profile.render_calls == [(config.OperationCode.EXEC_COMMAND, (command_line,))]
        assert dummy_connection.written == [rendered_payload.encode("utf-8")]

    def test_execute_command_send_request__renderer_returns_none__falls_back_to_raw_command_bytes(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """ExecuteCommand transmits raw UTF-8 command bytes when renderer returns None."""

        command_line = "id"
        dummy_profile.set_rendered_command(config.OperationCode.EXEC_COMMAND, None)

        dto = ExecuteCommandDTO(command_line=command_line)
        command = ExecuteCommand(dto)

        command.send_request(test_session)

        assert dummy_profile.render_calls == [(config.OperationCode.EXEC_COMMAND, (command_line,))]
        assert dummy_connection.written == [command_line.encode("utf-8")]

    def test_execute_command_send_request__renderer_returns_empty_string__falls_back_to_raw_command_bytes(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """ExecuteCommand transmits raw UTF-8 command bytes when renderer returns an empty string."""

        command_line = "ls -la"
        dummy_profile.set_rendered_command(config.OperationCode.EXEC_COMMAND, "")

        dto = ExecuteCommandDTO(command_line=command_line)
        command = ExecuteCommand(dto)

        command.send_request(test_session)

        assert dummy_profile.render_calls == [(config.OperationCode.EXEC_COMMAND, (command_line,))]
        assert dummy_connection.written == [command_line.encode("utf-8")]

    def test_execute_command_read_response__stream_chunks__forwards_all_chunks_to_view(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
    ) -> None:
        """ExecuteCommand reads all response chunks from connection and writes them to the view."""

        chunks = [b"uid=1000(dev) gid=1000(dev)\n", b"groups=1000(dev)\n"]
        dummy_connection.incoming_chunks = chunks

        dto = ExecuteCommandDTO(command_line="id")
        command = ExecuteCommand(dto)

        command.read_response(test_session)

        assert dummy_view.binary_data == chunks

    def test_execute_command_lifecycle__via_session_execute__transmits_and_streams_response(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """Executing ExecuteCommand via SessionContext coordinates both send_request and read_response."""

        command_line = "uname -r"
        rendered_command = "rendered_uname_output"
        output_chunks = [b"6.1.0-28-amd64\n"]

        dummy_profile.set_rendered_command(config.OperationCode.EXEC_COMMAND, rendered_command)
        dummy_connection.incoming_chunks = output_chunks

        dto = ExecuteCommandDTO(command_line=command_line)
        command = ExecuteCommand(dto)

        test_session.execute(command)

        assert dummy_profile.render_calls == [(config.OperationCode.EXEC_COMMAND, (command_line,))]
        assert dummy_connection.written == [rendered_command.encode("utf-8")]
        assert dummy_view.binary_data == output_chunks
