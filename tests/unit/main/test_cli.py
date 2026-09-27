from unittest.mock import patch

import pytest

from declusor import config, main, testing


def test_main_success(dummy_app: testing.DummyApplication) -> None:
    """Verify main returns 0 on successful application execution."""

    exit_code = main.run_terminal_app(["127.0.0.1", "9000"], application=dummy_app)
    assert exit_code == 0
    assert len(dummy_app.run_calls) == 1
    assert dummy_app.run_calls[0].host == "127.0.0.1"
    assert dummy_app.run_calls[0].port == 9000
    assert dummy_app.run_calls[0].kind == testing.DummyPlugin.name


def test_main_defaults_to_terminal_application_when_omitted(dummy_app: testing.DummyApplication) -> None:
    """Verify main creates a TerminalApplication by default when none is passed."""

    with patch("declusor.app.create_terminal_application", return_value=dummy_app):
        exit_code = main.run_terminal_app(["127.0.0.1", "9000"])
        assert exit_code == 0
        assert len(dummy_app.run_calls) == 1


def test_main_parser_error(
    dummy_app: testing.DummyApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify main returns 2 on ParserError and prints error to stderr."""

    exit_code = main.run_terminal_app(["--bad-option"], application=dummy_app)
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "parser error:" in captured.err


def test_main_declusor_exception(
    dummy_app: testing.DummyApplication,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify main returns 1 on general DeclusorException and prints error to stderr."""

    dummy_app.run_error = config.ConnectionError("network failed")
    exit_code = main.run_terminal_app(["127.0.0.1", "9000"], application=dummy_app)
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "declusor error: network failed" in captured.err


def test_main_keyboard_interrupt(dummy_app: testing.DummyApplication) -> None:
    """Verify main returns 0 on KeyboardInterrupt."""

    dummy_app.run_error = KeyboardInterrupt()
    exit_code = main.run_terminal_app(["127.0.0.1", "9000"], application=dummy_app)
    assert exit_code == 0


def test_main_explicit_cli_mode(dummy_app: testing.DummyApplication) -> None:
    """Verify main executes TerminalApplication when --mode cli is specified."""

    with patch("declusor.app.create_terminal_application", return_value=dummy_app):
        exit_code = main.run_terminal_app(["127.0.0.1", "9000", "--mode", "cli"])
        assert exit_code == 0
        assert len(dummy_app.run_calls) == 1


def test_main_unsupported_mode_prints_error_and_returns_1(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify main returns 1 and prints an error message when an unsupported mode is requested."""

    exit_code = main.run_terminal_app(["127.0.0.1", "9000", "--mode", "mcp"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Execution mode 'mcp' is not supported yet" in captured.err
