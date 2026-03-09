from typing import Any


class MockReadline:
    """A mock implementation of the readline library module."""

    def __init__(self) -> None:
        self.completer_delims = ""
        self.completer: Any = None
        self.binds: list[str] = []

    def set_completer_delims(self, delims: str) -> None:
        self.completer_delims = delims

    def set_completer(self, func: Any) -> None:
        self.completer = func

    def parse_and_bind(self, bind: str) -> None:
        self.binds.append(bind)
