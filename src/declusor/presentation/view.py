import sys

from declusor import contract


class TerminalView(contract.IView):
    """Terminal presentation view rendering messages to stdout and stderr."""

    def write_message(self, message: str, /) -> None:
        """Display a plain informational message to standard output.

        Args:
            message: The message string to display.
        """

        sys.stdout.write(message + "\n")
        sys.stdout.flush()

    def write_error(self, message: str | BaseException, /) -> None:
        """Display an error message to standard error with 'error: ' prefix.

        Args:
            message: Error description or exception to display.
        """

        sys.stderr.write(f"error: {message}\n")
        sys.stderr.flush()

    def write_warning(self, message: str | BaseException, /) -> None:
        """Display a warning message to standard error with 'warning: ' prefix.

        Args:
            message: Warning description or exception to display.
        """

        sys.stderr.write(f"warning: {message}\n")
        sys.stderr.flush()

    def write_info(self, message: str, /) -> None:
        """Display an informational notice to standard output with 'info: ' prefix.

        Args:
            message: Informational text to display.
        """

        sys.stdout.write(f"info: {message}\n")
        sys.stdout.flush()

    def write_success(self, message: str, /) -> None:
        """Display a success notice to standard output with 'success: ' prefix.

        Args:
            message: Success text to display.
        """

        sys.stdout.write(f"success: {message}\n")
        sys.stdout.flush()

    def write_binary_data(self, data: bytes, /) -> None:
        """Write raw binary data to standard output buffer.

        Args:
            data: Binary payload to write verbatim.
        """

        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
