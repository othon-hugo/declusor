from unittest.mock import patch

import pytest

from declusor import config, main, testing


def test_main_success(dummy_app: testing.DummyApplication) -> None:
    """Verify main returns 0 on successful application execution."""

    expected_options = testing.create_dummy_options(host="127.0.0.1", port=9000)
    dummy_app.parse_result = expected_options

    with patch("declusor.main.cli.create_application", return_value=dummy_app):
        exit_code = main.main(["127.0.0.1", "9000"])
        assert exit_code == 0
        assert dummy_app.parse_calls == [["127.0.0.1", "9000"]]
        assert dummy_app.run_calls == [expected_options]


def test_main_parser_error(
    dummy_app: testing.DummyApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify main returns 2 on ParserError and prints error to stderr."""

    dummy_app.parse_error = config.ParserError("invalid option")

    with patch("declusor.main.cli.create_application", return_value=dummy_app):
        exit_code = main.main(["--bad-option"])
        assert exit_code == 2
        captured = capsys.readouterr()
        assert "parser error: invalid option" in captured.err


def test_main_declusor_exception(
    dummy_app: testing.DummyApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify main returns 1 on general DeclusorException and prints error to stderr."""

    dummy_app.parse_error = config.ConnectionError("network failed")

    with patch("declusor.main.cli.create_application", return_value=dummy_app):
        exit_code = main.main(["127.0.0.1", "9000"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "declusor error: network failed" in captured.err


def test_main_keyboard_interrupt(dummy_app: testing.DummyApplication) -> None:
    """Verify main returns 0 on KeyboardInterrupt."""

    dummy_app.parse_error = KeyboardInterrupt()

    with patch("declusor.main.cli.create_application", return_value=dummy_app):
        exit_code = main.main(["127.0.0.1", "9000"])
        assert exit_code == 0
