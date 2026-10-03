"""Unit tests for UploadArguments and call_upload in declusor.controller.upload."""

from pathlib import Path
from typing import is_typeddict

import pytest

from declusor import config, contract, testing, util
from declusor.controller import upload as upload_module


class TestUploadArguments:
    """Tests verifying UploadArguments TypedDict invariants and contract compliance."""

    def test_upload_arguments__is_typeddict(self) -> None:
        """UploadArguments is a valid TypedDict type."""

        assert is_typeddict(upload_module.UploadArguments)

    def test_upload_arguments__declares_expected_fields(self) -> None:
        """UploadArguments specifies filepath and destination annotations."""

        annotations = upload_module.UploadArguments.__annotations__

        assert "filepath" in annotations
        assert annotations["filepath"] is str
        assert "destination" in annotations


class TestUploadController:
    """Tests verifying call_upload file reading, destination forwarding, and error propagation."""

    def test_call_upload__filepath_only__uploads_without_destination_argument(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_profile: testing.DummyConnectionProfile,
        dummy_view: testing.DummyView,
    ) -> None:
        """call_upload transmits Base64 file payload without destination when omitted."""

        test_file = tmp_path / "upload.bin"
        test_file.write_bytes(b"binary-content-12345")
        expected_b64 = util.convert_to_base64(b"binary-content-12345")
        dummy_profile.set_rendered_command(config.OperationCode.STORE_FILE, "rendered_upload")
        req = testing.create_dummy_controller_request(str(test_file), upload_module.UploadArguments)

        result = upload_module.call_upload(test_session, req)

        assert isinstance(result, contract.ControllerResult)
        assert result.action == contract.ControllerAction.CONTINUE
        assert dummy_connection.written == [b"rendered_upload"]
        assert dummy_profile.render_calls == [(config.OperationCode.STORE_FILE, (expected_b64,))]
        assert dummy_view.binary_data == [b"chunk1\n", b"chunk2\n"]

    def test_call_upload__filepath_and_destination__passes_destination_to_renderer(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """call_upload includes destination parameter in rendered operation command."""

        test_file = tmp_path / "upload.bin"
        test_file.write_bytes(b"payload")
        expected_b64 = util.convert_to_base64(b"payload")
        destination = "/tmp/target_remote.bin"
        dummy_profile.set_rendered_command(config.OperationCode.STORE_FILE, "rendered_dest_upload")
        req = testing.create_dummy_controller_request(
            f"{test_file} {destination}",
            upload_module.UploadArguments,
        )

        result = upload_module.call_upload(test_session, req)

        assert result.action == contract.ControllerAction.CONTINUE
        assert dummy_connection.written == [b"rendered_dest_upload"]
        assert dummy_profile.render_calls == [(config.OperationCode.STORE_FILE, (expected_b64, destination))]

    def test_call_upload__paths_with_spaces__parses_and_uploads_correctly(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """call_upload supports quoted file paths containing whitespace for both source and destination."""

        source_dir = tmp_path / "my folder"
        source_dir.mkdir()
        source_file = source_dir / "my data.bin"
        source_file.write_bytes(b"spaced payload")
        expected_b64 = util.convert_to_base64(b"spaced payload")
        destination = "/var/log/spaced target.bin"
        dummy_profile.set_rendered_command(config.OperationCode.STORE_FILE, "rendered_spaced_upload")
        req = testing.create_dummy_controller_request(
            f'"{source_file}" "{destination}"',
            upload_module.UploadArguments,
        )

        result = upload_module.call_upload(test_session, req)

        assert result.action == contract.ControllerAction.CONTINUE
        assert dummy_profile.render_calls == [(config.OperationCode.STORE_FILE, (expected_b64, destination))]

    def test_call_upload__empty_request_line__raises_parser_error(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """call_upload raises ParserError when filepath argument is missing."""

        req = testing.create_dummy_controller_request("", upload_module.UploadArguments)

        with pytest.raises(config.ParserError):
            upload_module.call_upload(test_session, req)

    def test_call_upload__whitespace_only_request_line__raises_parser_error(
        self,
        test_session: contract.SessionContext,
    ) -> None:
        """call_upload raises ParserError when request line consists only of whitespace."""

        req = testing.create_dummy_controller_request("   \t  \n  ", upload_module.UploadArguments)

        with pytest.raises(config.ParserError):
            upload_module.call_upload(test_session, req)

    def test_call_upload__nonexistent_file__raises_invalid_operation(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
    ) -> None:
        """call_upload raises InvalidOperation when local source file does not exist."""

        missing_file = tmp_path / "missing_file_87654.bin"
        req = testing.create_dummy_controller_request(str(missing_file), upload_module.UploadArguments)

        with pytest.raises(config.InvalidOperation):
            upload_module.call_upload(test_session, req)

    def test_call_upload__directory_source_path__raises_invalid_operation(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
    ) -> None:
        """call_upload raises InvalidOperation when local source path targets a directory."""

        target_dir = tmp_path / "upload_dir"
        target_dir.mkdir()
        req = testing.create_dummy_controller_request(str(target_dir), upload_module.UploadArguments)

        with pytest.raises(config.InvalidOperation):
            upload_module.call_upload(test_session, req)

    def test_call_upload__destination_with_control_characters__raises_command_validation_error(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
    ) -> None:
        """call_upload propagates CommandValidationError when destination contains illegal control characters."""

        test_file = tmp_path / "upload.bin"
        test_file.write_bytes(b"content")
        req = testing.create_dummy_controller_request(
            f'{test_file} "/remote/\x01invalid"',
            upload_module.UploadArguments,
        )

        with pytest.raises(config.CommandValidationError) as exc_info:
            upload_module.call_upload(test_session, req)

        assert exc_info.value.field == "destination"
        assert "\x01" in str(exc_info.value.value)

    def test_call_upload__connection_write_failure__propagates_exception(
        self,
        tmp_path: Path,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
    ) -> None:
        """call_upload propagates connection errors without swallowing them."""

        test_file = tmp_path / "upload.bin"
        test_file.write_bytes(b"content")
        dummy_connection.write_error = config.ConnectionError("Upload transport error")
        req = testing.create_dummy_controller_request(str(test_file), upload_module.UploadArguments)

        with pytest.raises(config.ConnectionError, match="Upload transport error"):
            upload_module.call_upload(test_session, req)
