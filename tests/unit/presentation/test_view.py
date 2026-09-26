from unittest.mock import patch

import pytest

from declusor import presentation


def test_terminal_view_write_message(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify write_message outputs to stdout with newline."""

    view = presentation.TerminalView()
    view.write_message("hello world")
    captured = capsys.readouterr()
    assert captured.out == "hello world\n"


def test_terminal_view_write_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify write_error outputs to stderr with 'error: ' prefix."""

    view = presentation.TerminalView()
    view.write_error("something failed")
    captured = capsys.readouterr()
    assert captured.err == "error: something failed\n"


def test_terminal_view_write_warning(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify write_warning outputs to stderr with 'warning: ' prefix."""

    view = presentation.TerminalView()
    view.write_warning("something fishy")
    captured = capsys.readouterr()
    assert captured.err == "warning: something fishy\n"


def test_terminal_view_write_info(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify write_info outputs to stdout with 'info: ' prefix."""

    view = presentation.TerminalView()
    view.write_info("informational update")
    captured = capsys.readouterr()
    assert captured.out == "info: informational update\n"


def test_terminal_view_write_success(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify write_success outputs to stdout with 'success: ' prefix."""

    view = presentation.TerminalView()
    view.write_success("operation succeeded")
    captured = capsys.readouterr()
    assert captured.out == "success: operation succeeded\n"


def test_terminal_view_write_binary_data() -> None:
    """Verify write_binary_data writes bytes to stdout.buffer."""

    view = presentation.TerminalView()

    with patch("sys.stdout.buffer.write") as mock_write, patch("sys.stdout.buffer.flush") as mock_flush:
        view.write_binary_data(b"binary payload")
        mock_write.assert_called_once_with(b"binary payload")
        mock_flush.assert_called_once()
