from collections.abc import Sequence
from pathlib import Path

from declusor import interface


class MockConsole(interface.IConsole):
    """A mock implementation of IConsole for testing."""

    def __init__(self) -> None:
        self.setup_completer_called_with: list[Sequence[str]] = []
        self.enable_history_called_with: list[Path] = []
        self.lines_to_read: list[str | type[BaseException] | BaseException] = []
        self.written_messages: list[str] = []
        self.written_binary_data: list[bytes] = []
        self.written_error_messages: list[str | BaseException] = []
        self.written_warning_messages: list[str | BaseException] = []

    def setup_completer(self, commands: Sequence[str], /) -> None:
        self.setup_completer_called_with.append(commands)

    def enable_history(self, history_file: Path, /) -> None:
        self.enable_history_called_with.append(history_file)

    def read_line(self, prompt: str = "", /) -> str:
        if self.lines_to_read:
            val = self.lines_to_read.pop(0)

            if isinstance(val, Exception) or isinstance(val, BaseException):
                raise val

            if isinstance(val, type) and issubclass(val, BaseException):
                raise val()

            return val

        return ""

    def read_stripped_line(self, prompt: str = "", /) -> str:
        line = self.read_line(prompt)

        return line.strip()

    def write_message(self, message: str, /) -> None:
        self.written_messages.append(message)

    def write_binary_data(self, message: bytes, /) -> None:
        self.written_binary_data.append(message)

    def write_error_message(self, message: str | BaseException, /) -> None:
        self.written_error_messages.append(message)

    def write_warning_message(self, message: str | BaseException, /) -> None:
        self.written_warning_messages.append(message)
