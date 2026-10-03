"""Unit tests for TerminalView presentation component in declusor.presentation.view."""

import io
import sys
from typing import BinaryIO

import pytest

from declusor import config, contract, presentation


class FlushTrackingTextIO(io.StringIO):
    """In-memory text stream recording the number of explicit flush invocations."""

    def __init__(self, initial_value: str = "") -> None:
        super().__init__(initial_value)
        self.flush_count: int = 0

    def flush(self) -> None:
        self.flush_count += 1
        super().flush()


class FlushTrackingBinaryIO(io.BytesIO):
    """In-memory binary stream recording the number of explicit flush invocations."""

    def __init__(self, initial_bytes: bytes = b"") -> None:
        super().__init__(initial_bytes)
        self.flush_count: int = 0

    def flush(self) -> None:
        self.flush_count += 1
        super().flush()


class CustomStreamWithBuffer(io.StringIO):
    """Text stream possessing a dedicated underlying binary buffer attribute."""

    def __init__(self) -> None:
        super().__init__()
        self.buffer: BinaryIO = io.BytesIO()


class TestTerminalViewInitialization:
    """Tests verifying TerminalView stream binding and contract conformance."""

    def test_terminal_view_contract_conformance__implements_iview(self) -> None:
        """TerminalView satisfies the IView contract interface."""

        view = presentation.TerminalView()

        assert isinstance(view, contract.IView)

    def test_terminal_view_default_initialization__binds_to_system_streams(self) -> None:
        """TerminalView defaults stdout, stderr, and binary buffer to standard sys streams."""

        view = presentation.TerminalView()

        assert view._stdout is sys.stdout
        assert view._stderr is sys.stderr
        assert view._buffer is getattr(sys.stdout, "buffer", sys.stdout.buffer)

    def test_terminal_view_injected_streams__binds_custom_streams(self) -> None:
        """TerminalView retains injected custom text and binary streams."""

        stdout = io.StringIO()
        stderr = io.StringIO()
        buffer = io.BytesIO()

        view = presentation.TerminalView(stdout=stdout, stderr=stderr, buffer=buffer)

        assert view._stdout is stdout
        assert view._stderr is stderr
        assert view._buffer is buffer

    def test_terminal_view_buffer_fallback_from_stdout__uses_stdout_buffer_attribute(self) -> None:
        """TerminalView extracts the buffer attribute from injected stdout when buffer is omitted."""

        stdout_with_buf = CustomStreamWithBuffer()

        view = presentation.TerminalView(stdout=stdout_with_buf)

        assert view._buffer is stdout_with_buf.buffer

    def test_terminal_view_buffer_fallback_when_stdout_lacks_buffer__uses_sys_stdout_buffer(self) -> None:
        """TerminalView falls back to sys.stdout.buffer when stdout stream lacks a buffer attribute."""

        plain_stdout = io.StringIO()

        view = presentation.TerminalView(stdout=plain_stdout)

        assert view._buffer is sys.stdout.buffer

    def test_terminal_view_buffer_fallback_when_sys_stdout_lacks_buffer__uses_in_memory_bytes_io(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """TerminalView falls back to an in-memory BytesIO buffer when sys.stdout lacks a buffer attribute."""

        monkeypatch.setattr(sys, "stdout", io.StringIO())

        view = presentation.TerminalView()

        assert isinstance(view._buffer, io.BytesIO)

    def test_terminal_view_buffer_fallback_when_stdout_and_sys_stdout_lack_buffer__uses_in_memory_bytes_io(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """TerminalView safely uses BytesIO buffer when both injected stdout and sys.stdout lack buffer."""

        monkeypatch.setattr(sys, "stdout", io.StringIO())
        custom_stdout = io.StringIO()

        view = presentation.TerminalView(stdout=custom_stdout)

        assert isinstance(view._buffer, io.BytesIO)

    def test_terminal_view_buffer_when_stdout_has_buffer_and_sys_stdout_lacks_buffer__uses_stdout_buffer(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """TerminalView preserves stdout.buffer without accessing sys.stdout.buffer when sys.stdout lacks it."""

        monkeypatch.setattr(sys, "stdout", io.StringIO())
        stdout_with_buf = CustomStreamWithBuffer()

        view = presentation.TerminalView(stdout=stdout_with_buf)

        assert view._buffer is stdout_with_buf.buffer


class TestTerminalViewTextOutputs:
    """Tests verifying standard text output methods and formatting on TerminalView."""

    def test_terminal_view_write_message__writes_message_with_newline_to_stdout_and_flushes(self) -> None:
        """write_message writes message content followed by newline to stdout and flushes."""

        stdout = FlushTrackingTextIO()
        view = presentation.TerminalView(stdout=stdout)

        view.write_message("status report")

        assert stdout.getvalue() == "status report\n"
        assert stdout.flush_count == 1

    def test_terminal_view_write_message_empty_string__writes_only_newline(self) -> None:
        """write_message with an empty string writes only a single newline character."""

        stdout = FlushTrackingTextIO()
        view = presentation.TerminalView(stdout=stdout)

        view.write_message("")

        assert stdout.getvalue() == "\n"
        assert stdout.flush_count == 1

    def test_terminal_view_write_info__writes_with_info_prefix_and_newline_to_stdout_and_flushes(self) -> None:
        """write_info prefixes message with 'info: ' and flushes stdout."""

        stdout = FlushTrackingTextIO()
        view = presentation.TerminalView(stdout=stdout)

        view.write_info("system ready")

        assert stdout.getvalue() == "info: system ready\n"
        assert stdout.flush_count == 1

    def test_terminal_view_write_success__writes_with_success_prefix_and_newline_to_stdout_and_flushes(self) -> None:
        """write_success prefixes message with 'success: ' and flushes stdout."""

        stdout = FlushTrackingTextIO()
        view = presentation.TerminalView(stdout=stdout)

        view.write_success("transaction confirmed")

        assert stdout.getvalue() == "success: transaction confirmed\n"
        assert stdout.flush_count == 1

    def test_terminal_view_write_message_multiline__writes_all_lines_to_stdout_and_flushes(self) -> None:
        """write_message writes multiline message preserving line breaks and flushes."""

        stdout = FlushTrackingTextIO()
        view = presentation.TerminalView(stdout=stdout)

        view.write_message("first line\nsecond line\nthird line")

        assert stdout.getvalue() == "first line\nsecond line\nthird line\n"
        assert stdout.flush_count == 1

    def test_terminal_view_write_info_multiline__writes_prefixed_multiline_to_stdout_and_flushes(self) -> None:
        """write_info prefixes multiline text with 'info: ' and flushes."""

        stdout = FlushTrackingTextIO()
        view = presentation.TerminalView(stdout=stdout)

        view.write_info("step 1\nstep 2")

        assert stdout.getvalue() == "info: step 1\nstep 2\n"
        assert stdout.flush_count == 1

    def test_terminal_view_write_success_multiline__writes_prefixed_multiline_to_stdout_and_flushes(self) -> None:
        """write_success prefixes multiline text with 'success: ' and flushes."""

        stdout = FlushTrackingTextIO()
        view = presentation.TerminalView(stdout=stdout)

        view.write_success("task done\ncleanup completed")

        assert stdout.getvalue() == "success: task done\ncleanup completed\n"
        assert stdout.flush_count == 1


class TestTerminalViewErrorAndWarningOutputs:
    """Tests verifying error and warning reporting to stderr on TerminalView."""

    def test_terminal_view_write_error_with_string__writes_with_error_prefix_to_stderr_and_flushes(self) -> None:
        """write_error with string prefixes message with 'error: ' on stderr and flushes."""

        stderr = FlushTrackingTextIO()
        view = presentation.TerminalView(stderr=stderr)

        view.write_error("unhandled fault")

        assert stderr.getvalue() == "error: unhandled fault\n"
        assert stderr.flush_count == 1

    def test_terminal_view_write_error_with_standard_exception__formats_exception_message(self) -> None:
        """write_error formats BaseException instances as 'error: <str(exception)>'."""

        stderr = FlushTrackingTextIO()
        view = presentation.TerminalView(stderr=stderr)

        view.write_error(ValueError("invalid dimension"))

        assert stderr.getvalue() == "error: invalid dimension\n"
        assert stderr.flush_count == 1

    def test_terminal_view_write_error_with_declusor_exception__formats_domain_exception(self) -> None:
        """write_error formats DeclusorException instances with their complete message."""

        stderr = FlushTrackingTextIO()
        view = presentation.TerminalView(stderr=stderr)

        view.write_error(config.CommandError("process aborted"))

        assert stderr.getvalue() == "error: command error: process aborted\n"
        assert stderr.flush_count == 1

    def test_terminal_view_write_warning_with_string__writes_with_warning_prefix_to_stderr_and_flushes(self) -> None:
        """write_warning with string prefixes message with 'warning: ' on stderr and flushes."""

        stderr = FlushTrackingTextIO()
        view = presentation.TerminalView(stderr=stderr)

        view.write_warning("resource low")

        assert stderr.getvalue() == "warning: resource low\n"
        assert stderr.flush_count == 1

    def test_terminal_view_write_warning_with_standard_exception__formats_exception_message(self) -> None:
        """write_warning formats BaseException instances as 'warning: <str(exception)>'."""

        stderr = FlushTrackingTextIO()
        view = presentation.TerminalView(stderr=stderr)

        view.write_warning(RuntimeError("transient degradation"))

        assert stderr.getvalue() == "warning: transient degradation\n"
        assert stderr.flush_count == 1

    def test_terminal_view_write_warning_with_declusor_warning__formats_domain_warning(self) -> None:
        """write_warning formats DeclusorWarning instances with warning prefix."""

        stderr = FlushTrackingTextIO()
        view = presentation.TerminalView(stderr=stderr)

        view.write_warning(config.DeclusorWarning("experimental feature active"))

        assert stderr.getvalue() == "warning: experimental feature active\n"
        assert stderr.flush_count == 1

    def test_terminal_view_write_error_multiline__writes_prefixed_multiline_to_stderr_and_flushes(self) -> None:
        """write_error prefixes multiline error text with 'error: ' on stderr and flushes."""

        stderr = FlushTrackingTextIO()
        view = presentation.TerminalView(stderr=stderr)

        view.write_error("traceback start\ninner frame\nfatal condition")

        assert stderr.getvalue() == "error: traceback start\ninner frame\nfatal condition\n"
        assert stderr.flush_count == 1

    def test_terminal_view_write_warning_multiline__writes_prefixed_multiline_to_stderr_and_flushes(self) -> None:
        """write_warning prefixes multiline warning text with 'warning: ' on stderr and flushes."""

        stderr = FlushTrackingTextIO()
        view = presentation.TerminalView(stderr=stderr)

        view.write_warning("deprecated API\nuse new signature")

        assert stderr.getvalue() == "warning: deprecated API\nuse new signature\n"
        assert stderr.flush_count == 1


class TestTerminalViewBinaryOutput:
    """Tests verifying raw binary streaming on TerminalView."""

    def test_terminal_view_write_binary_data__writes_verbatim_bytes_and_flushes(self) -> None:
        """write_binary_data writes exact byte payload to the binary buffer and flushes."""

        buffer = FlushTrackingBinaryIO()
        view = presentation.TerminalView(buffer=buffer)

        view.write_binary_data(b"\x00\x01\x02\xff")

        assert buffer.getvalue() == b"\x00\x01\x02\xff"
        assert buffer.flush_count == 1

    def test_terminal_view_write_binary_data_empty_bytes__flushes_without_error(self) -> None:
        """write_binary_data with empty byte payload executes cleanly and flushes."""

        buffer = FlushTrackingBinaryIO()
        view = presentation.TerminalView(buffer=buffer)

        view.write_binary_data(b"")

        assert buffer.getvalue() == b""
        assert buffer.flush_count == 1

    def test_terminal_view_write_binary_data_large_chunk__writes_entire_payload(self) -> None:
        """write_binary_data writes large binary chunks completely."""

        buffer = FlushTrackingBinaryIO()
        view = presentation.TerminalView(buffer=buffer)
        large_payload = b"A" * 65536

        view.write_binary_data(large_payload)

        assert buffer.getvalue() == large_payload
        assert buffer.flush_count == 1


class TestTerminalViewStreamIsolation:
    """Tests verifying channel separation between stdout, stderr, and binary buffer."""

    def test_terminal_view_stream_routing__keeps_stdout_and_stderr_strictly_separated(self) -> None:
        """Text written to stdout does not leak into stderr, and vice-versa."""

        stdout = io.StringIO()
        stderr = io.StringIO()
        buffer = io.BytesIO()
        view = presentation.TerminalView(stdout=stdout, stderr=stderr, buffer=buffer)

        view.write_message("stdout line")
        view.write_info("stdout info")
        view.write_success("stdout success")

        assert stderr.getvalue() == ""
        assert buffer.getvalue() == b""

        view.write_error("stderr error")
        view.write_warning("stderr warning")

        assert stdout.getvalue() == "stdout line\ninfo: stdout info\nsuccess: stdout success\n"
        assert stderr.getvalue() == "error: stderr error\nwarning: stderr warning\n"
        assert buffer.getvalue() == b""

    def test_terminal_view_capsys_integration__verifies_unconfigured_instance_outputs_to_pytest_capsys(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Default TerminalView routes properly to standard process streams captured by capsys."""

        view = presentation.TerminalView()

        view.write_message("captured stdout")
        view.write_error("captured stderr")

        captured = capsys.readouterr()
        assert captured.out == "captured stdout\n"
        assert captured.err == "error: captured stderr\n"


class TestTerminalViewPositionalParameters:
    """Tests verifying positional-only parameter enforcement across TerminalView methods."""

    def test_terminal_view_write_message_keyword_call__raises_type_error(self) -> None:
        """write_message enforces positional-only argument passing for message."""

        view = presentation.TerminalView()

        with pytest.raises(TypeError, match="positional-only"):
            view.write_message(message="hello")  # type: ignore[call-arg]

    def test_terminal_view_write_error_keyword_call__raises_type_error(self) -> None:
        """write_error enforces positional-only argument passing for message."""

        view = presentation.TerminalView()

        with pytest.raises(TypeError, match="positional-only"):
            view.write_error(message="fatal")  # type: ignore[call-arg]

    def test_terminal_view_write_warning_keyword_call__raises_type_error(self) -> None:
        """write_warning enforces positional-only argument passing for message."""

        view = presentation.TerminalView()

        with pytest.raises(TypeError, match="positional-only"):
            view.write_warning(message="caution")  # type: ignore[call-arg]

    def test_terminal_view_write_info_keyword_call__raises_type_error(self) -> None:
        """write_info enforces positional-only argument passing for message."""

        view = presentation.TerminalView()

        with pytest.raises(TypeError, match="positional-only"):
            view.write_info(message="notice")  # type: ignore[call-arg]

    def test_terminal_view_write_success_keyword_call__raises_type_error(self) -> None:
        """write_success enforces positional-only argument passing for message."""

        view = presentation.TerminalView()

        with pytest.raises(TypeError, match="positional-only"):
            view.write_success(message="done")  # type: ignore[call-arg]

    def test_terminal_view_write_binary_data_keyword_call__raises_type_error(self) -> None:
        """write_binary_data enforces positional-only argument passing for data."""

        view = presentation.TerminalView()

        with pytest.raises(TypeError, match="positional-only"):
            view.write_binary_data(data=b"chunk")  # type: ignore[call-arg]
