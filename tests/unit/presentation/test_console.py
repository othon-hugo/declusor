from unittest.mock import patch

import pytest

from declusor import presentation


def test_console_write_message(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify write_message outputs to stdout with newline."""

    console = presentation.Console()

    console.write_message("hello world")
    captured = capsys.readouterr()
    assert captured.out == "hello world\n"


def test_console_write_error_message(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify write_error_message outputs to stderr with 'error: ' prefix."""

    console = presentation.Console()
    console.write_error_message("something failed")
    captured = capsys.readouterr()
    assert captured.err == "error: something failed\n"


def test_console_write_warning_message(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify write_warning_message outputs to stderr with 'warning: ' prefix."""

    console = presentation.Console()
    console.write_warning_message("something fishy")
    captured = capsys.readouterr()
    assert captured.err == "warning: something fishy\n"


def test_console_write_binary_data() -> None:
    """Verify write_binary_data writes bytes to stdout.buffer."""

    console = presentation.Console()

    with patch("sys.stdout.buffer.write") as mock_write, patch("sys.stdout.buffer.flush") as mock_flush:
        console.write_binary_data(b"binary payload")
        mock_write.assert_called_once_with(b"binary payload")
        mock_flush.assert_called_once()


def test_console_read_line() -> None:
    """Verify read_line appends newline to input()."""

    console = presentation.Console()

    with patch("builtins.input", return_value="command arg"):
        assert console.read_line("> ") == "command arg\n"


def test_console_read_stripped_line() -> None:
    """Verify read_stripped_line strips leading/trailing whitespace."""

    console = presentation.Console()

    with patch("builtins.input", return_value="  command arg  "):
        assert console.read_stripped_line("> ") == "command arg"
