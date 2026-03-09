from typing import Any


class MockReadline:
    """A mock implementation of the readline library module."""

    line_buffer = "ls test"

    def __init__(self) -> None:
        self.completer_delims = ""
        self.completer: Any = None
        self.binds: list[str] = []
        self.history_read: list[str] = []
        self.history_written: list[str] = []

    def set_completer_delims(self, delims: str) -> None:
        self.completer_delims = delims

    def set_completer(self, func: Any) -> None:
        self.completer = func

    def parse_and_bind(self, bind: str) -> None:
        self.binds.append(bind)

    def get_line_buffer(self) -> str:
        return self.line_buffer

    def read_history_file(self, filename: str) -> None:
        if filename.endswith("missing_hist"):
            raise FileNotFoundError()

        self.history_read.append(filename)

    def write_history_file(self, filename: str) -> None:
        self.history_written.append(filename)
