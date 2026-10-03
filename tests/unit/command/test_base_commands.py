"""Unit tests for BaseStreamCommand and BaseFileCommand abstractions in declusor.command."""

from pathlib import Path

import pytest

from declusor import config, contract, testing, util
from declusor.command.base import BaseFileCommand, BaseStreamCommand
from declusor.command.execute_file import ExecuteFileDTO


class ConcreteStreamCommand(BaseStreamCommand):
    """Concrete test double implementing send_request for BaseStreamCommand."""

    def send_request(self, session: contract.SessionContext, /) -> None:
        """Fulfill abstract send_request with a no-op implementation."""


class ConcreteFileCommand(BaseFileCommand[ExecuteFileDTO]):
    """Concrete test double subclass of BaseFileCommand with default arguments."""

    def __init__(
        self,
        dto: ExecuteFileDTO,
        /,
        opcode: BaseFileCommand._SupportedOperationCodes = config.OperationCode.EXEC_FILE,
    ) -> None:
        """Initialize concrete file command with DTO and operational code."""

        super().__init__(dto, opcode=opcode)


class CustomArgsFileCommand(BaseFileCommand[ExecuteFileDTO]):
    """Concrete test double of BaseFileCommand overriding _operation_arguments."""

    def __init__(
        self,
        dto: ExecuteFileDTO,
        extra_arguments: tuple[str, ...],
        /,
        opcode: BaseFileCommand._SupportedOperationCodes = config.OperationCode.STORE_FILE,
    ) -> None:
        """Initialize custom arguments file command with extra operation arguments."""

        super().__init__(dto, opcode=opcode)
        self._extra_args = extra_arguments

    def _operation_arguments(self) -> tuple[str, ...]:
        """Return injected extra arguments for renderer."""

        return self._extra_args


class TestBaseStreamCommand:
    """Tests verifying BaseStreamCommand stream consumption and presentation invariants."""

    def test_base_stream_command__direct_instantiation__raises_type_error(self) -> None:
        """Direct instantiation of BaseStreamCommand raises TypeError due to abstract send_request."""

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseStreamCommand()  # type: ignore[abstract]

    def test_base_stream_command_read_response__empty_stream__does_not_write_to_view(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
    ) -> None:
        """BaseStreamCommand handles an empty connection stream without writing binary data to view."""

        dummy_connection.incoming_chunks = []
        command = ConcreteStreamCommand()

        command.read_response(test_session)

        assert dummy_view.binary_data == []

    def test_base_stream_command_read_response__single_chunk__writes_chunk_to_view(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
    ) -> None:
        """BaseStreamCommand consumes a single chunk and forwards it directly to the view."""

        single_chunk = b"single line output\n"
        dummy_connection.incoming_chunks = [single_chunk]
        command = ConcreteStreamCommand()

        command.read_response(test_session)

        assert dummy_view.binary_data == [single_chunk]

    def test_base_stream_command_read_response__multiple_chunks__preserves_order_and_content(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
    ) -> None:
        """BaseStreamCommand preserves chunk sequence and exact content when reading multiple chunks."""

        stream_chunks = [b"first chunk\n", b"second chunk\n", b"third chunk\n"]
        dummy_connection.incoming_chunks = stream_chunks
        command = ConcreteStreamCommand()

        command.read_response(test_session)

        assert dummy_view.binary_data == stream_chunks
        assert len(dummy_view.binary_data) == 3


class TestBaseFileCommand:
    """Tests verifying BaseFileCommand payload preparation, template rendering, and error handling."""

    def test_base_file_command_operation_arguments__default_implementation__returns_empty_tuple(
        self,
        tmp_path: Path,
    ) -> None:
        """BaseFileCommand._operation_arguments default implementation returns an empty tuple."""

        script_file = tmp_path / "script.sh"
        script_file.write_text("echo 'testing'")
        dto = ExecuteFileDTO(filepath=script_file)
        command = ConcreteFileCommand(dto)

        arguments = command._operation_arguments()

        assert arguments == ()

    def test_base_file_command_send_request__valid_file__reads_encodes_and_transmits_payload(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """BaseFileCommand loads file, encodes base64, invokes renderer, and writes UTF-8 bytes."""

        file_content = b"echo 'declusor-payload'"
        script_file = tmp_path / "script.sh"
        script_file.write_bytes(file_content)

        expected_b64 = util.convert_to_base64(file_content)
        rendered_command = "rendered_exec_file_payload"
        dummy_profile.set_rendered_command(config.OperationCode.EXEC_FILE, rendered_command)

        dto = ExecuteFileDTO(filepath=script_file)
        command = ConcreteFileCommand(dto, opcode=config.OperationCode.EXEC_FILE)

        command.send_request(test_session)

        assert dummy_profile.render_calls == [(config.OperationCode.EXEC_FILE, (expected_b64,))]
        assert dummy_connection.written == [rendered_command.encode("utf-8")]

    def test_base_file_command_send_request__overridden_operation_arguments__passes_extra_args_to_renderer(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """Subclass overriding _operation_arguments passes additional arguments to render_operation_command."""

        file_content = b"sample binary payload content"
        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(file_content)

        expected_b64 = util.convert_to_base64(file_content)
        destination_path = "/remote/dest/payload.bin"
        permission_flag = "--executable"
        rendered_command = "rendered_store_file_payload"
        dummy_profile.set_rendered_command(config.OperationCode.STORE_FILE, rendered_command)

        dto = ExecuteFileDTO(filepath=payload_file)
        command = CustomArgsFileCommand(
            dto,
            (destination_path, permission_flag),
            opcode=config.OperationCode.STORE_FILE,
        )

        command.send_request(test_session)

        assert dummy_profile.render_calls == [(config.OperationCode.STORE_FILE, (expected_b64, destination_path, permission_flag))]
        assert dummy_connection.written == [rendered_command.encode("utf-8")]

    def test_base_file_command_send_request__renderer_returns_none__raises_invalid_operation(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """BaseFileCommand raises InvalidOperation when profile renderer returns None."""

        script_file = tmp_path / "script.sh"
        script_file.write_text("echo 'fail'")

        dummy_profile.set_rendered_command(config.OperationCode.EXEC_FILE, None)

        dto = ExecuteFileDTO(filepath=script_file)
        command = ConcreteFileCommand(dto, opcode=config.OperationCode.EXEC_FILE)

        with pytest.raises(config.InvalidOperation, match="Failed to generate script data for the file operation") as exc_info:
            command.send_request(test_session)

        assert exc_info.value.description == "Failed to generate script data for the file operation."

    def test_base_file_command_send_request__renderer_returns_empty_string__raises_invalid_operation(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """BaseFileCommand raises InvalidOperation when profile renderer returns an empty string."""

        script_file = tmp_path / "script.sh"
        script_file.write_text("echo 'fail'")

        dummy_profile.set_rendered_command(config.OperationCode.EXEC_FILE, "")

        dto = ExecuteFileDTO(filepath=script_file)
        command = ConcreteFileCommand(dto, opcode=config.OperationCode.EXEC_FILE)

        with pytest.raises(config.InvalidOperation, match="Failed to generate script data for the file operation") as exc_info:
            command.send_request(test_session)

        assert exc_info.value.description == "Failed to generate script data for the file operation."

    def test_base_file_command_lifecycle__via_session_execute__sends_request_and_reads_response(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """Executing BaseFileCommand through SessionContext executes full request-response lifecycle."""

        file_content = b"echo 'lifecycle test'"
        script_file = tmp_path / "script.sh"
        script_file.write_bytes(file_content)

        rendered_command = "rendered_lifecycle_file_payload"
        incoming_chunks = [b"lifecycle output 1\n", b"lifecycle output 2\n"]
        dummy_profile.set_rendered_command(config.OperationCode.EXEC_FILE, rendered_command)
        dummy_connection.incoming_chunks = incoming_chunks

        dto = ExecuteFileDTO(filepath=script_file)
        command = ConcreteFileCommand(dto, opcode=config.OperationCode.EXEC_FILE)

        test_session.execute(command)

        assert dummy_connection.written == [rendered_command.encode("utf-8")]
        assert dummy_view.binary_data == incoming_chunks
