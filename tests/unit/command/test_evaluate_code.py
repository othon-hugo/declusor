"""Unit tests for EvaluateCodeDTO and EvaluateCode in declusor.command."""

from dataclasses import FrozenInstanceError

import pytest

from declusor import config, contract, testing
from declusor.command.evaluate_code import EvaluateCode, EvaluateCodeDTO


class TestEvaluateCodeDTO:
    """Tests verifying EvaluateCodeDTO validation, immutability, and equality invariants."""

    @pytest.mark.parametrize(
        "valid_code",
        [
            "print('hello')",
            "x = 1 + 1\nprint(x)",
            "import os\nprint(os.getpid())",
            "def test():\n    return 42\nprint(test())",
        ],
    )
    def test_evaluate_code_dto_init__valid_code__preserves_code(self, valid_code: str) -> None:
        """EvaluateCodeDTO accepts non-empty code strings without modification."""

        dto = EvaluateCodeDTO(code=valid_code)

        assert dto.code == valid_code

    @pytest.mark.parametrize(
        "invalid_code",
        [
            "",
            " ",
            "\t",
            "\n",
            "\t\n",
            "\r\n",
            "   \n\t  \r\n   ",
        ],
    )
    def test_evaluate_code_dto_init__empty_or_whitespace__raises_command_validation_error(
        self,
        invalid_code: str,
    ) -> None:
        """EvaluateCodeDTO rejects empty or whitespace-only code strings with CommandValidationError."""

        with pytest.raises(config.CommandValidationError) as exc_info:
            EvaluateCodeDTO(code=invalid_code)

        assert exc_info.value.field == "code"
        assert exc_info.value.value == invalid_code
        assert isinstance(exc_info.value, config.DeclusorException)
        assert isinstance(exc_info.value, config.CommandError)
        assert "Code cannot be empty." in str(exc_info.value)

    def test_evaluate_code_dto_immutability__reassign_attribute__raises_frozen_instance_error(self) -> None:
        """EvaluateCodeDTO is frozen and raises FrozenInstanceError on attribute reassignment."""

        dto = EvaluateCodeDTO(code="print('hello')")

        with pytest.raises(FrozenInstanceError):
            dto.code = "print('modified')"  # type: ignore[misc]

    def test_evaluate_code_dto_equality__identical_code__evaluates_equal(self) -> None:
        """EvaluateCodeDTO instances with identical code strings compare equal."""

        dto_first = EvaluateCodeDTO(code="print('value')")
        dto_second = EvaluateCodeDTO(code="print('value')")

        assert dto_first == dto_second
        assert hash(dto_first) == hash(dto_second)


class TestEvaluateCode:
    """Tests verifying EvaluateCode request transmission, renderer fallbacks, and streaming."""

    def test_evaluate_code_send_request__successful_render__transmits_rendered_payload(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_renderer: testing.DummyOperationRenderer,
    ) -> None:
        """EvaluateCode invokes renderer with EXEC_CODE opcode and transmits rendered payload."""

        code = "print('hello from client')"
        rendered_payload = "rendered_python_code_eval"
        dummy_renderer.set_rendered_command(config.OperationCode.EXEC_CODE, rendered_payload)

        dto = EvaluateCodeDTO(code=code)
        command = EvaluateCode(dto)

        command.send_request(test_session)

        assert dummy_renderer.render_calls == [(config.OperationCode.EXEC_CODE, (code,))]
        assert dummy_connection.written == [rendered_payload.encode("utf-8")]

    def test_evaluate_code_send_request__renderer_returns_none__falls_back_to_raw_code_bytes(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_renderer: testing.DummyOperationRenderer,
    ) -> None:
        """EvaluateCode transmits raw UTF-8 code bytes when renderer returns None."""

        code = "print('raw_code_fallback')"
        dummy_renderer.set_rendered_command(config.OperationCode.EXEC_CODE, None)

        dto = EvaluateCodeDTO(code=code)
        command = EvaluateCode(dto)

        command.send_request(test_session)

        assert dummy_renderer.render_calls == [(config.OperationCode.EXEC_CODE, (code,))]
        assert dummy_connection.written == [code.encode("utf-8")]

    def test_evaluate_code_send_request__renderer_returns_empty_string__falls_back_to_raw_code_bytes(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_renderer: testing.DummyOperationRenderer,
    ) -> None:
        """EvaluateCode transmits raw UTF-8 code bytes when renderer returns an empty string."""

        code = "print('empty_string_fallback')"
        dummy_renderer.set_rendered_command(config.OperationCode.EXEC_CODE, "")

        dto = EvaluateCodeDTO(code=code)
        command = EvaluateCode(dto)

        command.send_request(test_session)

        assert dummy_renderer.render_calls == [(config.OperationCode.EXEC_CODE, (code,))]
        assert dummy_connection.written == [code.encode("utf-8")]

    def test_evaluate_code_read_response__stream_chunks__forwards_all_chunks_to_view(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
    ) -> None:
        """EvaluateCode reads all response chunks from connection and writes them to the view."""

        chunks = [b"evaluation result line 1\n", b"evaluation result line 2\n"]
        dummy_connection.incoming_chunks = chunks

        dto = EvaluateCodeDTO(code="print('evaluating')")
        command = EvaluateCode(dto)

        command.read_response(test_session)

        assert dummy_view.binary_data == chunks

    def test_evaluate_code_lifecycle__via_session_execute__transmits_and_streams_response(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
        dummy_renderer: testing.DummyOperationRenderer,
    ) -> None:
        """Executing EvaluateCode via SessionContext coordinates both send_request and read_response."""

        code = "print('full_lifecycle')"
        rendered_command = "rendered_lifecycle_code_eval"
        output_chunks = [b"full_lifecycle\n"]

        dummy_renderer.set_rendered_command(config.OperationCode.EXEC_CODE, rendered_command)
        dummy_connection.incoming_chunks = output_chunks

        dto = EvaluateCodeDTO(code=code)
        command = EvaluateCode(dto)

        test_session.execute(command)

        assert dummy_renderer.render_calls == [(config.OperationCode.EXEC_CODE, (code,))]
        assert dummy_connection.written == [rendered_command.encode("utf-8")]
        assert dummy_view.binary_data == output_chunks
