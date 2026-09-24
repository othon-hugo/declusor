from collections.abc import Sequence
from pathlib import Path

from declusor import contract


class DummyConsole(contract.IConsole):
    """Fully-typed in-memory console capturing all output and simulating input."""

    def __init__(self, inputs: Sequence[str] | None = None) -> None:
        self._inputs: list[str] = list(inputs) if inputs is not None else []
        self.input_exception: BaseException | None = None
        self.messages: list[str] = []
        self.binary_data: list[bytes] = []
        self.errors: list[str | BaseException] = []
        self.warnings: list[str | BaseException] = []
        self.prompts: list[str] = []
        self.history_files: list[Path] = []
        self.configured_completers: list[list[str]] = []

    def feed_inputs(self, *lines: str) -> None:
        """Enqueue simulated input lines for read_line and read_stripped_line."""

        self._inputs.extend(lines)

    def setup_completer(self, commands: Sequence[str], /) -> None:
        """Capture registered completion commands."""

        self.configured_completers.append(list(commands))

    def enable_history(self, history_file: Path, /) -> None:
        """Record the configured history file path."""

        self.history_files.append(history_file)

    def read_line(self, prompt: str = "", /) -> str:
        """Return the next queued input line or newline if queue is empty."""

        self.prompts.append(prompt)

        if self.input_exception is not None:
            exc = self.input_exception
            self.input_exception = None
            raise exc

        if not self._inputs:
            return "\n"

        line = self._inputs.pop(0)

        return line if line.endswith("\n") else f"{line}\n"

    def read_stripped_line(self, prompt: str = "", /) -> str:
        """Return the next queued stripped input line or empty string if queue is empty."""

        self.prompts.append(prompt)

        if self.input_exception is not None:
            exc = self.input_exception
            self.input_exception = None
            raise exc

        if not self._inputs:
            return ""

        return self._inputs.pop(0).strip()

    def write_line(self, message: str = "", /) -> None:
        """Capture standard output message."""

        self.messages.append(message)

    def write_binary_data(self, data: bytes, /) -> None:
        """Capture transmitted raw bytes."""

        self.binary_data.append(data)

    def write_error(self, message: str | BaseException, /) -> None:
        """Capture error output message or exception."""

        self.errors.append(message)

    def write_success(self, message: str, /) -> None:
        """Capture success output message."""

        self.messages.append(f"SUCCESS: {message}")

    def write_warning(self, message: str | BaseException, /) -> None:
        """Capture warning output message or exception."""

        self.warnings.append(message)

    def write_info(self, message: str, /) -> None:
        """Capture info output message."""

        self.messages.append(f"INFO: {message}")

    def clear(self) -> None:
        """Simulate clearing the terminal screen."""

        self.messages.append("[CLEAR]")

    def write_message(self, message: str, /) -> None:
        """Capture generic message."""

        self.messages.append(message)

    def write_error_message(self, message: str | BaseException, /) -> None:
        """Capture error output message or exception."""

        self.errors.append(message)

    def write_warning_message(self, message: str | BaseException, /) -> None:
        """Capture warning output message or exception."""

        self.warnings.append(message)
