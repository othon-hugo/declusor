from unittest.mock import patch

from declusor import presentation


def test_terminal_input_source_read_command() -> None:
    """Verify read_command strips whitespace from input()."""

    source = presentation.TerminalInputSource()

    with patch("builtins.input", return_value="  command arg  "):
        assert source.read_command("> ") == "command arg"


def test_terminal_input_source_read_raw() -> None:
    """Verify read_raw appends newline to input()."""

    source = presentation.TerminalInputSource()

    with patch("builtins.input", return_value="command arg"):
        assert source.read_raw("> ") == "command arg\n"
