from unittest.mock import MagicMock, patch

from declusor import config
from declusor.main.cli import main


def test_main_success() -> None:
    """Verify main returns 0 on successful application execution."""

    mock_app = MagicMock()
    mock_app.parse.return_value = {"mock": "options"}

    with patch("declusor.main.cli.create_application", return_value=mock_app):
        exit_code = main(["127.0.0.1", "9000"])
        assert exit_code == 0
        mock_app.run.assert_called_once_with({"mock": "options"})


def test_main_parser_error(capsys) -> None:
    """Verify main returns 2 on ParserError and prints error to stderr."""

    mock_app = MagicMock()
    mock_app.parse.side_effect = config.ParserError("invalid option")

    with patch("declusor.main.cli.create_application", return_value=mock_app):
        exit_code = main(["--bad-option"])
        assert exit_code == 2
        captured = capsys.readouterr()
        assert "parser error: invalid option" in captured.err


def test_main_declusor_exception(capsys) -> None:
    """Verify main returns 1 on general DeclusorException and prints error to stderr."""

    mock_app = MagicMock()
    mock_app.parse.side_effect = config.ConnectionError("network failed")

    with patch("declusor.main.cli.create_application", return_value=mock_app):
        exit_code = main(["127.0.0.1", "9000"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "declusor error: network failed" in captured.err


def test_main_keyboard_interrupt() -> None:
    """Verify main returns 0 on KeyboardInterrupt."""

    mock_app = MagicMock()
    mock_app.parse.side_effect = KeyboardInterrupt

    with patch("declusor.main.cli.create_application", return_value=mock_app):
        exit_code = main(["127.0.0.1", "9000"])
        assert exit_code == 0
