"""Unit tests for ExecuteFileDTO, ExecuteFile, UploadFileDTO, and UploadFile in declusor.command."""

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Final

import pytest

from declusor import config, contract, testing, util
from declusor.command.base import BaseFileCommand
from declusor.command.execute_file import ExecuteFile, ExecuteFileDTO
from declusor.command.upload_file import UploadFile, UploadFileDTO

# [Constants & Invariants]

TEST_SCRIPT_CONTENT: Final[bytes] = b"#!/bin/sh\necho 'running test script'\n"
TEST_BINARY_CONTENT: Final[bytes] = b"\x00\x01\x02\x03\x04\xfe\xff"
RENDERED_EXEC_PAYLOAD: Final[str] = "rendered_exec_script_payload"
RENDERED_UPLOAD_PAYLOAD: Final[str] = "rendered_upload_payload"
VALID_DESTINATION_PATH: Final[str] = "/remote/target/destination.bin"
PADDED_DESTINATION_PATH: Final[str] = "   /remote/target/destination.bin \t "


class TestExecuteFileDTO:
    """Tests verifying ExecuteFileDTO validation, path resolution, immutability, and equality invariants."""

    def test_execute_file_dto_init__valid_path_instance__normalizes_to_resolved_path(self, tmp_path: Path) -> None:
        """ExecuteFileDTO accepts a valid existing Path instance and normalizes to a resolved Path."""

        script_file = tmp_path / "script.sh"
        script_file.write_bytes(TEST_SCRIPT_CONTENT)

        dto = ExecuteFileDTO(filepath=script_file)

        assert isinstance(dto.filepath, Path)
        assert dto.filepath == script_file.resolve()

    def test_execute_file_dto_init__valid_str_path__normalizes_to_resolved_path(self, tmp_path: Path) -> None:
        """ExecuteFileDTO accepts a valid existing string file path and normalizes to a resolved Path."""

        script_file = tmp_path / "script.sh"
        script_file.write_bytes(TEST_SCRIPT_CONTENT)

        dto = ExecuteFileDTO(filepath=str(script_file))

        assert isinstance(dto.filepath, Path)
        assert dto.filepath == script_file.resolve()

    def test_execute_file_dto_init__relative_path__normalizes_to_resolved_path(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """ExecuteFileDTO normalizes relative file paths to absolute resolved Paths."""

        script_file = tmp_path / "local_script.sh"
        script_file.write_bytes(TEST_SCRIPT_CONTENT)
        monkeypatch.chdir(tmp_path)

        dto = ExecuteFileDTO(filepath=Path("local_script.sh"))

        assert dto.filepath == script_file.resolve()
        assert dto.filepath.is_absolute()

    def test_execute_file_dto_init__missing_file__raises_invalid_operation(self, tmp_path: Path) -> None:
        """ExecuteFileDTO rejects a non-existent file path with InvalidOperation."""

        missing_file = tmp_path / "nonexistent.sh"

        with pytest.raises(config.InvalidOperation) as exc_info:
            ExecuteFileDTO(filepath=missing_file)

        assert isinstance(exc_info.value, config.StorageValidationError)
        assert "does not exist" in str(exc_info.value)

    def test_execute_file_dto_init__directory_path__raises_invalid_operation(self, tmp_path: Path) -> None:
        """ExecuteFileDTO rejects a directory path with InvalidOperation."""

        directory_path = tmp_path / "scripts_dir"
        directory_path.mkdir()

        with pytest.raises(config.InvalidOperation) as exc_info:
            ExecuteFileDTO(filepath=directory_path)

        assert isinstance(exc_info.value, config.StorageValidationError)
        assert "is not a file" in str(exc_info.value)

    @pytest.mark.parametrize(
        "invalid_path",
        [
            "",
            " ",
            "\t",
            "\n",
            "\t\n",
            "\r\n",
            "   \t\n   ",
        ],
    )
    def test_execute_file_dto_init__empty_or_whitespace__raises_command_validation_error(
        self,
        invalid_path: str,
    ) -> None:
        """ExecuteFileDTO rejects empty or whitespace-only paths with CommandValidationError."""

        with pytest.raises(config.CommandValidationError) as exc_info:
            ExecuteFileDTO(filepath=invalid_path)

        assert exc_info.value.field == "filepath"
        assert exc_info.value.value == invalid_path
        assert isinstance(exc_info.value, config.InvalidOperation)
        assert isinstance(exc_info.value, config.CommandError)
        assert "File path cannot be empty." in str(exc_info.value)

    @pytest.mark.parametrize(
        "invalid_path",
        [
            "/tmp/script\x00.sh",
            "test\x00_exec.sh",
        ],
    )
    def test_execute_file_dto_init__null_bytes__raises_command_validation_error(
        self,
        invalid_path: str,
    ) -> None:
        """ExecuteFileDTO rejects file paths containing null bytes with CommandValidationError."""

        with pytest.raises(config.CommandValidationError) as exc_info:
            ExecuteFileDTO(filepath=invalid_path)

        assert exc_info.value.field == "filepath"
        assert exc_info.value.value == invalid_path
        assert isinstance(exc_info.value, config.InvalidOperation)
        assert isinstance(exc_info.value, config.CommandError)
        assert "File path cannot contain null bytes." in str(exc_info.value)

    def test_execute_file_dto_immutability__reassign_attribute__raises_frozen_instance_error(
        self,
        tmp_path: Path,
    ) -> None:
        """ExecuteFileDTO is frozen and raises FrozenInstanceError on attribute reassignment."""

        script_file = tmp_path / "script.sh"
        script_file.write_bytes(TEST_SCRIPT_CONTENT)

        dto = ExecuteFileDTO(filepath=script_file)

        with pytest.raises(FrozenInstanceError):
            dto.filepath = tmp_path / "other.sh"  # type: ignore[misc]

    def test_execute_file_dto_equality__identical_paths__evaluates_equal(self, tmp_path: Path) -> None:
        """ExecuteFileDTO instances with identical resolved paths compare equal."""

        script_file = tmp_path / "script.sh"
        script_file.write_bytes(TEST_SCRIPT_CONTENT)

        dto_first = ExecuteFileDTO(filepath=script_file)
        dto_second = ExecuteFileDTO(filepath=str(script_file))

        assert dto_first == dto_second
        assert hash(dto_first) == hash(dto_second)

    def test_execute_file_dto_equality__different_paths__evaluates_unequal(self, tmp_path: Path) -> None:
        """ExecuteFileDTO instances with different paths compare unequal."""

        file_first = tmp_path / "script_1.sh"
        file_first.write_bytes(TEST_SCRIPT_CONTENT)
        file_second = tmp_path / "script_2.sh"
        file_second.write_bytes(TEST_SCRIPT_CONTENT)

        dto_first = ExecuteFileDTO(filepath=file_first)
        dto_second = ExecuteFileDTO(filepath=file_second)

        assert dto_first != dto_second


class TestExecuteFile:
    """Tests verifying ExecuteFile request transmission, opcode binding, error handling, and streaming."""

    def test_execute_file_inheritance__subclasses_base_file_command(self) -> None:
        """ExecuteFile inherits from BaseFileCommand parameterized with ExecuteFileDTO."""

        assert issubclass(ExecuteFile, BaseFileCommand)

    def test_execute_file_init__sets_exec_file_opcode(self, tmp_path: Path) -> None:
        """ExecuteFile initializes with the EXEC_FILE operation code."""

        script_file = tmp_path / "script.sh"
        script_file.write_bytes(TEST_SCRIPT_CONTENT)

        dto = ExecuteFileDTO(filepath=script_file)
        command = ExecuteFile(dto)

        assert command._opcode == config.OperationCode.EXEC_FILE

    def test_execute_file_send_request__successful_render__reads_encodes_and_transmits(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """ExecuteFile reads file content, converts to base64, renders payload, and transmits to connection."""

        script_file = tmp_path / "script.sh"
        script_file.write_bytes(TEST_SCRIPT_CONTENT)
        dummy_profile.set_rendered_command(config.OperationCode.EXEC_FILE, RENDERED_EXEC_PAYLOAD)

        dto = ExecuteFileDTO(filepath=script_file)
        command = ExecuteFile(dto)

        command.send_request(test_session)

        expected_b64 = util.convert_to_base64(TEST_SCRIPT_CONTENT)
        assert dummy_profile.render_calls == [(config.OperationCode.EXEC_FILE, (expected_b64,))]
        assert dummy_connection.written == [RENDERED_EXEC_PAYLOAD.encode("utf-8")]

    def test_execute_file_send_request__renderer_returns_none__raises_invalid_operation(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """ExecuteFile raises InvalidOperation when the renderer returns None."""

        script_file = tmp_path / "script.sh"
        script_file.write_bytes(TEST_SCRIPT_CONTENT)
        dummy_profile.set_rendered_command(config.OperationCode.EXEC_FILE, None)

        dto = ExecuteFileDTO(filepath=script_file)
        command = ExecuteFile(dto)

        with pytest.raises(config.InvalidOperation, match="Failed to generate script data for the file operation."):
            command.send_request(test_session)

    def test_execute_file_send_request__renderer_returns_empty_string__raises_invalid_operation(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """ExecuteFile raises InvalidOperation when the renderer returns an empty string."""

        script_file = tmp_path / "script.sh"
        script_file.write_bytes(TEST_SCRIPT_CONTENT)
        dummy_profile.set_rendered_command(config.OperationCode.EXEC_FILE, "")

        dto = ExecuteFileDTO(filepath=script_file)
        command = ExecuteFile(dto)

        with pytest.raises(config.InvalidOperation, match="Failed to generate script data for the file operation."):
            command.send_request(test_session)

    def test_execute_file_read_response__stream_chunks__forwards_all_chunks_to_view(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
    ) -> None:
        """ExecuteFile forwards streamed output chunks from connection to view."""

        script_file = tmp_path / "script.sh"
        script_file.write_bytes(TEST_SCRIPT_CONTENT)
        stream_chunks = [b"script output line 1\n", b"script output line 2\n"]
        dummy_connection.incoming_chunks = stream_chunks

        dto = ExecuteFileDTO(filepath=script_file)
        command = ExecuteFile(dto)

        command.read_response(test_session)

        assert dummy_view.binary_data == stream_chunks

    def test_execute_file_lifecycle__via_session_execute__transmits_and_streams_chunks(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """ExecuteFile executes complete lifecycle via SessionContext, transmitting payload and streaming output."""

        script_file = tmp_path / "script.sh"
        script_file.write_bytes(TEST_SCRIPT_CONTENT)
        dummy_profile.set_rendered_command(config.OperationCode.EXEC_FILE, RENDERED_EXEC_PAYLOAD)
        stream_chunks = [b"execution chunk 1\n", b"execution chunk 2\n"]
        dummy_connection.incoming_chunks = stream_chunks

        dto = ExecuteFileDTO(filepath=script_file)
        command = ExecuteFile(dto)

        test_session.execute(command)

        expected_b64 = util.convert_to_base64(TEST_SCRIPT_CONTENT)
        assert dummy_profile.render_calls == [(config.OperationCode.EXEC_FILE, (expected_b64,))]
        assert dummy_connection.written == [RENDERED_EXEC_PAYLOAD.encode("utf-8")]
        assert dummy_view.binary_data == stream_chunks


class TestUploadFileDTO:
    """Tests verifying UploadFileDTO validation, path resolution, immutability, and equality invariants."""

    def test_upload_file_dto_init__valid_filepath_without_destination__sets_destination_none(
        self,
        tmp_path: Path,
    ) -> None:
        """UploadFileDTO accepts a valid file path and sets destination to None by default."""

        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)

        dto = UploadFileDTO(filepath=payload_file)

        assert isinstance(dto.filepath, Path)
        assert dto.filepath == payload_file.resolve()
        assert dto.destination is None

    def test_upload_file_dto_init__valid_filepath_with_clean_destination__preserves_destination(
        self,
        tmp_path: Path,
    ) -> None:
        """UploadFileDTO accepts a valid file path and preserves a clean remote destination string."""

        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)

        dto = UploadFileDTO(filepath=payload_file, destination=VALID_DESTINATION_PATH)

        assert dto.filepath == payload_file.resolve()
        assert dto.destination == VALID_DESTINATION_PATH

    def test_upload_file_dto_init__valid_filepath_with_padded_destination__normalizes_stripped_destination(
        self,
        tmp_path: Path,
    ) -> None:
        """UploadFileDTO strips leading and trailing whitespace from the destination path."""

        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)

        dto = UploadFileDTO(filepath=payload_file, destination=PADDED_DESTINATION_PATH)

        assert dto.destination == VALID_DESTINATION_PATH

    def test_upload_file_dto_init__str_filepath__normalizes_to_resolved_path(self, tmp_path: Path) -> None:
        """UploadFileDTO accepts string file path and normalizes to a resolved Path."""

        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)

        dto = UploadFileDTO(filepath=str(payload_file))

        assert isinstance(dto.filepath, Path)
        assert dto.filepath == payload_file.resolve()

    def test_upload_file_dto_init__relative_filepath__normalizes_to_resolved_path(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """UploadFileDTO normalizes relative file paths to absolute resolved Paths."""

        payload_file = tmp_path / "local_payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)
        monkeypatch.chdir(tmp_path)

        dto = UploadFileDTO(filepath=Path("local_payload.bin"))

        assert dto.filepath == payload_file.resolve()
        assert dto.filepath.is_absolute()

    def test_upload_file_dto_init__missing_file__raises_invalid_operation(self, tmp_path: Path) -> None:
        """UploadFileDTO rejects a non-existent file path with InvalidOperation."""

        missing_file = tmp_path / "missing_payload.bin"

        with pytest.raises(config.InvalidOperation) as exc_info:
            UploadFileDTO(filepath=missing_file)

        assert isinstance(exc_info.value, config.StorageValidationError)
        assert "does not exist" in str(exc_info.value)

    def test_upload_file_dto_init__directory_path__raises_invalid_operation(self, tmp_path: Path) -> None:
        """UploadFileDTO rejects a directory path with InvalidOperation."""

        directory_path = tmp_path / "payloads_dir"
        directory_path.mkdir()

        with pytest.raises(config.InvalidOperation) as exc_info:
            UploadFileDTO(filepath=directory_path)

        assert isinstance(exc_info.value, config.StorageValidationError)
        assert "is not a file" in str(exc_info.value)

    @pytest.mark.parametrize(
        "invalid_path",
        [
            "",
            " ",
            "\t",
            "\n",
            "\t\n",
            "\r\n",
            "   \t\n   ",
        ],
    )
    def test_upload_file_dto_init__empty_or_whitespace_filepath__raises_command_validation_error(
        self,
        invalid_path: str,
    ) -> None:
        """UploadFileDTO rejects empty or whitespace-only file paths with CommandValidationError."""

        with pytest.raises(config.CommandValidationError) as exc_info:
            UploadFileDTO(filepath=invalid_path)

        assert exc_info.value.field == "filepath"
        assert exc_info.value.value == invalid_path
        assert isinstance(exc_info.value, config.InvalidOperation)
        assert isinstance(exc_info.value, config.CommandError)
        assert "File path cannot be empty." in str(exc_info.value)

    @pytest.mark.parametrize(
        "invalid_path",
        [
            "/tmp/payload\x00.bin",
            "null\x00_data.bin",
        ],
    )
    def test_upload_file_dto_init__filepath_containing_null_bytes__raises_command_validation_error(
        self,
        invalid_path: str,
    ) -> None:
        """UploadFileDTO rejects file paths containing null bytes with CommandValidationError."""

        with pytest.raises(config.CommandValidationError) as exc_info:
            UploadFileDTO(filepath=invalid_path)

        assert exc_info.value.field == "filepath"
        assert exc_info.value.value == invalid_path
        assert isinstance(exc_info.value, config.InvalidOperation)
        assert isinstance(exc_info.value, config.CommandError)
        assert "File path cannot contain null bytes." in str(exc_info.value)

    @pytest.mark.parametrize(
        "invalid_dest",
        [
            "",
            " ",
            "\t",
            "\n",
            "\r\n",
            "   \t   \r\n   ",
        ],
    )
    def test_upload_file_dto_init__empty_or_whitespace_destination__raises_command_validation_error(
        self,
        tmp_path: Path,
        invalid_dest: str,
    ) -> None:
        """UploadFileDTO rejects empty or whitespace-only destinations with CommandValidationError."""

        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)

        with pytest.raises(config.CommandValidationError) as exc_info:
            UploadFileDTO(filepath=payload_file, destination=invalid_dest)

        assert exc_info.value.field == "destination"
        assert exc_info.value.value == invalid_dest
        assert isinstance(exc_info.value, config.InvalidOperation)
        assert isinstance(exc_info.value, config.CommandError)
        assert "Destination path cannot be empty." in str(exc_info.value)

    @pytest.mark.parametrize(
        "invalid_dest",
        [
            "/tmp/out\x00.bin",
            "dest\x00",
            "/path/with/\x00/null",
        ],
    )
    def test_upload_file_dto_init__destination_containing_null_bytes__raises_command_validation_error(
        self,
        tmp_path: Path,
        invalid_dest: str,
    ) -> None:
        """UploadFileDTO rejects destination paths containing null bytes with CommandValidationError."""

        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)

        with pytest.raises(config.CommandValidationError) as exc_info:
            UploadFileDTO(filepath=payload_file, destination=invalid_dest)

        assert exc_info.value.field == "destination"
        assert exc_info.value.value == invalid_dest
        assert isinstance(exc_info.value, config.InvalidOperation)
        assert isinstance(exc_info.value, config.CommandError)
        assert "Destination path cannot contain null bytes." in str(exc_info.value)

    @pytest.mark.parametrize(
        "invalid_dest",
        [
            "/tmp/out\n.bin",
            "/tmp/out\r.bin",
            "/tmp/out\x1b.bin",
            "/tmp/out\x07.bin",
            "/tmp/out\x1f.bin",
        ],
    )
    def test_upload_file_dto_init__destination_containing_control_characters__raises_command_validation_error(
        self,
        tmp_path: Path,
        invalid_dest: str,
    ) -> None:
        """UploadFileDTO rejects destination paths containing control characters or newlines."""

        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)

        with pytest.raises(config.CommandValidationError) as exc_info:
            UploadFileDTO(filepath=payload_file, destination=invalid_dest)

        assert exc_info.value.field == "destination"
        assert exc_info.value.value == invalid_dest
        assert isinstance(exc_info.value, config.InvalidOperation)
        assert isinstance(exc_info.value, config.CommandError)
        assert "Destination path cannot contain control characters or newlines." in str(exc_info.value)

    def test_upload_file_dto_immutability__reassign_attribute__raises_frozen_instance_error(
        self,
        tmp_path: Path,
    ) -> None:
        """UploadFileDTO is frozen and raises FrozenInstanceError on attribute reassignment."""

        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)

        dto = UploadFileDTO(filepath=payload_file, destination=VALID_DESTINATION_PATH)

        with pytest.raises(FrozenInstanceError):
            dto.filepath = tmp_path / "other.bin"  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            dto.destination = "/other/path.bin"  # type: ignore[misc]

    def test_upload_file_dto_equality__identical_fields__evaluates_equal(self, tmp_path: Path) -> None:
        """UploadFileDTO instances with identical fields evaluate equal."""

        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)

        dto_first = UploadFileDTO(filepath=payload_file, destination=VALID_DESTINATION_PATH)
        dto_second = UploadFileDTO(filepath=str(payload_file), destination=PADDED_DESTINATION_PATH)

        assert dto_first == dto_second
        assert hash(dto_first) == hash(dto_second)

    def test_upload_file_dto_equality__different_destinations__evaluates_unequal(self, tmp_path: Path) -> None:
        """UploadFileDTO instances with different destinations evaluate unequal."""

        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)

        dto_first = UploadFileDTO(filepath=payload_file, destination=None)
        dto_second = UploadFileDTO(filepath=payload_file, destination=VALID_DESTINATION_PATH)

        assert dto_first != dto_second


class TestUploadFile:
    """Tests verifying UploadFile request transmission, opcode binding, argument generation, and streaming."""

    def test_upload_file_inheritance__subclasses_base_file_command(self) -> None:
        """UploadFile inherits from BaseFileCommand parameterized with UploadFileDTO."""

        assert issubclass(UploadFile, BaseFileCommand)

    def test_upload_file_init__sets_store_file_opcode(self, tmp_path: Path) -> None:
        """UploadFile initializes with the STORE_FILE operation code."""

        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)

        dto = UploadFileDTO(filepath=payload_file)
        command = UploadFile(dto)

        assert command._opcode == config.OperationCode.STORE_FILE

    def test_upload_file_operation_arguments__without_destination__returns_empty_tuple(
        self,
        tmp_path: Path,
    ) -> None:
        """UploadFile._operation_arguments returns an empty tuple when destination is None."""

        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)

        dto = UploadFileDTO(filepath=payload_file, destination=None)
        command = UploadFile(dto)

        assert command._operation_arguments() == ()

    def test_upload_file_operation_arguments__with_destination__returns_destination_tuple(
        self,
        tmp_path: Path,
    ) -> None:
        """UploadFile._operation_arguments returns a single-element tuple containing the destination."""

        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)

        dto = UploadFileDTO(filepath=payload_file, destination=VALID_DESTINATION_PATH)
        command = UploadFile(dto)

        assert command._operation_arguments() == (VALID_DESTINATION_PATH,)

    def test_upload_file_send_request__without_destination__invokes_renderer_with_encoded_content_only(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """UploadFile invokes renderer with STORE_FILE opcode and encoded file content when destination is None."""

        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)
        dummy_profile.set_rendered_command(config.OperationCode.STORE_FILE, RENDERED_UPLOAD_PAYLOAD)

        dto = UploadFileDTO(filepath=payload_file, destination=None)
        command = UploadFile(dto)

        command.send_request(test_session)

        expected_b64 = util.convert_to_base64(TEST_BINARY_CONTENT)
        assert dummy_profile.render_calls == [(config.OperationCode.STORE_FILE, (expected_b64,))]
        assert dummy_connection.written == [RENDERED_UPLOAD_PAYLOAD.encode("utf-8")]

    def test_upload_file_send_request__with_destination__invokes_renderer_with_content_and_destination(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """UploadFile invokes renderer with STORE_FILE opcode, encoded content, and destination when provided."""

        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)
        dummy_profile.set_rendered_command(config.OperationCode.STORE_FILE, RENDERED_UPLOAD_PAYLOAD)

        dto = UploadFileDTO(filepath=payload_file, destination=VALID_DESTINATION_PATH)
        command = UploadFile(dto)

        command.send_request(test_session)

        expected_b64 = util.convert_to_base64(TEST_BINARY_CONTENT)
        assert dummy_profile.render_calls == [
            (config.OperationCode.STORE_FILE, (expected_b64, VALID_DESTINATION_PATH)),
        ]
        assert dummy_connection.written == [RENDERED_UPLOAD_PAYLOAD.encode("utf-8")]

    def test_upload_file_send_request__renderer_returns_none__raises_invalid_operation(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """UploadFile raises InvalidOperation when the renderer returns None."""

        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)
        dummy_profile.set_rendered_command(config.OperationCode.STORE_FILE, None)

        dto = UploadFileDTO(filepath=payload_file)
        command = UploadFile(dto)

        with pytest.raises(config.InvalidOperation, match="Failed to generate script data for the file operation."):
            command.send_request(test_session)

    def test_upload_file_send_request__renderer_returns_empty_string__raises_invalid_operation(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """UploadFile raises InvalidOperation when the renderer returns an empty string."""

        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)
        dummy_profile.set_rendered_command(config.OperationCode.STORE_FILE, "")

        dto = UploadFileDTO(filepath=payload_file)
        command = UploadFile(dto)

        with pytest.raises(config.InvalidOperation, match="Failed to generate script data for the file operation."):
            command.send_request(test_session)

    def test_upload_file_read_response__stream_chunks__forwards_all_chunks_to_view(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
    ) -> None:
        """UploadFile forwards streamed output chunks from connection to view."""

        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)
        stream_chunks = [b"upload complete\n", b"bytes written: 7\n"]
        dummy_connection.incoming_chunks = stream_chunks

        dto = UploadFileDTO(filepath=payload_file)
        command = UploadFile(dto)

        command.read_response(test_session)

        assert dummy_view.binary_data == stream_chunks

    def test_upload_file_lifecycle__without_destination__transmits_and_streams_chunks(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """UploadFile executes complete lifecycle via SessionContext without destination, streaming output."""

        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)
        dummy_profile.set_rendered_command(config.OperationCode.STORE_FILE, RENDERED_UPLOAD_PAYLOAD)
        stream_chunks = [b"upload ack chunk 1\n", b"upload ack chunk 2\n"]
        dummy_connection.incoming_chunks = stream_chunks

        dto = UploadFileDTO(filepath=payload_file, destination=None)
        command = UploadFile(dto)

        test_session.execute(command)

        expected_b64 = util.convert_to_base64(TEST_BINARY_CONTENT)
        assert dummy_profile.render_calls == [(config.OperationCode.STORE_FILE, (expected_b64,))]
        assert dummy_connection.written == [RENDERED_UPLOAD_PAYLOAD.encode("utf-8")]
        assert dummy_view.binary_data == stream_chunks

    def test_upload_file_lifecycle__with_destination__transmits_and_streams_chunks(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """UploadFile executes complete lifecycle via SessionContext with destination, streaming output."""

        payload_file = tmp_path / "payload.bin"
        payload_file.write_bytes(TEST_BINARY_CONTENT)
        dummy_profile.set_rendered_command(config.OperationCode.STORE_FILE, RENDERED_UPLOAD_PAYLOAD)
        stream_chunks = [b"upload dest ack 1\n", b"upload dest ack 2\n"]
        dummy_connection.incoming_chunks = stream_chunks

        dto = UploadFileDTO(filepath=payload_file, destination=VALID_DESTINATION_PATH)
        command = UploadFile(dto)

        test_session.execute(command)

        expected_b64 = util.convert_to_base64(TEST_BINARY_CONTENT)
        assert dummy_profile.render_calls == [
            (config.OperationCode.STORE_FILE, (expected_b64, VALID_DESTINATION_PATH)),
        ]
        assert dummy_connection.written == [RENDERED_UPLOAD_PAYLOAD.encode("utf-8")]
        assert dummy_view.binary_data == stream_chunks
