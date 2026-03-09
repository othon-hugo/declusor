"""Tests for the ``declusor.interface.console`` module."""

from pathlib import Path

import pytest

from declusor.interface import console


# =============================================================================
# Dummies/Mocks
# =============================================================================

class DummyConsole(console.IConsole):
    """Null-implementation subclass delegating attributes to the interface."""

    def setup_completer(self, commands: list[str]) -> None:
        super().setup_completer(commands)

    def enable_history(self, history_file: Path) -> None:
        super().enable_history(history_file)

    def read_line(self, prompt: str = "") -> str:
        return super().read_line(prompt)

    def read_stripped_line(self, prompt: str = "") -> str:
        return super().read_stripped_line(prompt)

    def write_message(self, message: str) -> None:
        super().write_message(message)

    def write_binary_data(self, message: bytes) -> None:
        super().write_binary_data(message)

    def write_error_message(self, message: str | BaseException) -> None:
        super().write_error_message(message)

    def write_warning_message(self, message: str | BaseException) -> None:
        super().write_warning_message(message)


# =============================================================================
# Tests: IConsole (Interface contract)
# =============================================================================

def test_iconsole_methods_raise_not_implemented_error() -> None:
    """Calling abstract execution and formatting methods on ``IConsole`` must raise a ``NotImplementedError``."""

    # ARRANGE: Test environment object
    dummy = DummyConsole()

    # ACT & ASSERT: Ensure the abstract base correctly signals unimplemented routines
    with pytest.raises(NotImplementedError):
        dummy.setup_completer([])

    with pytest.raises(NotImplementedError):
        dummy.enable_history(Path("mock"))

    with pytest.raises(NotImplementedError):
        dummy.read_line()

    with pytest.raises(NotImplementedError):
        dummy.read_stripped_line()

    with pytest.raises(NotImplementedError):
        dummy.write_message("msg")

    with pytest.raises(NotImplementedError):
        dummy.write_binary_data(b"data")

    with pytest.raises(NotImplementedError):
        dummy.write_error_message(Exception("err"))

    with pytest.raises(NotImplementedError):
        dummy.write_warning_message(Exception("warn"))
