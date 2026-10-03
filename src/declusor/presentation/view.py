import io
import sys
from typing import BinaryIO, TextIO

from declusor import contract


class TerminalView(contract.IView):
    """Terminal presentation view rendering messages to stdout and stderr."""

    def __init__(
        self,
        stdout: TextIO | None = None,
        stderr: TextIO | None = None,
        buffer: BinaryIO | None = None,
    ) -> None:
        self._stdout: TextIO = stdout if stdout is not None else sys.stdout
        self._stderr: TextIO = stderr if stderr is not None else sys.stderr

        if buffer is not None:
            self._buffer: BinaryIO = buffer
        else:
            stdout_buffer = getattr(self._stdout, "buffer", None)
            if stdout_buffer is not None:
                self._buffer = stdout_buffer
            else:
                sys_buffer = getattr(sys.stdout, "buffer", None)
                self._buffer = sys_buffer if sys_buffer is not None else io.BytesIO()

    def write_message(self, message: str, /) -> None:
        """Display a plain informational message to standard output.

        Args:
            message: The message string to display.
        """

        self._stdout.write(message + "\n")
        self._stdout.flush()

    def write_error(self, message: str | BaseException, /) -> None:
        """Display an error message to standard error with 'error: ' prefix.

        Args:
            message: Error description or exception to display.
        """

        self._stderr.write(f"error: {message}\n")
        self._stderr.flush()

    def write_warning(self, message: str | BaseException, /) -> None:
        """Display a warning message to standard error with 'warning: ' prefix.

        Args:
            message: Warning description or exception to display.
        """

        self._stderr.write(f"warning: {message}\n")
        self._stderr.flush()

    def write_info(self, message: str, /) -> None:
        """Display an informational notice to standard output with 'info: ' prefix.

        Args:
            message: Informational text to display.
        """

        self._stdout.write(f"info: {message}\n")
        self._stdout.flush()

    def write_success(self, message: str, /) -> None:
        """Display a success notice to standard output with 'success: ' prefix.

        Args:
            message: Success text to display.
        """

        self._stdout.write(f"success: {message}\n")
        self._stdout.flush()

    def write_binary_data(self, data: bytes, /) -> None:
        """Write raw binary data to standard output buffer.

        Args:
            data: Binary payload to write verbatim.
        """

        self._buffer.write(data)
        self._buffer.flush()
