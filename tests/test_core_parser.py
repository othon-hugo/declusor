"""Tests for ``declusor.core.parser.Parser``.

Covers initialization, the custom ``error`` method (raises ``ParserError``
instead of calling ``sys.exit``), ``get_formatter_class``, argument parsing,
and the contrast with ``argparse.ArgumentParser``.
"""

import pytest

# =============================================================================
# Tests: Parser initialization
# =============================================================================


def test_init_accepts_prog_name() -> None:
    """``Parser(prog="cmd")`` must set ``self.prog`` to ``"cmd"``."""


def test_init_defaults_add_help_to_false() -> None:
    """Without an explicit ``add_help`` argument, ``-h`` / ``--help`` must not be recognized."""


def test_init_with_add_help_true() -> None:
    """``Parser(add_help=True)`` must register ``-h`` / ``--help`` flags."""


# =============================================================================
# Tests: Parser.error
# =============================================================================


def test_error_raises_parser_error() -> None:
    """``error("msg")`` must raise ``ParserError``, not ``SystemExit``."""


def test_error_includes_message_in_exception() -> None:
    """The ``ParserError`` exception must contain the error message."""


def test_error_message_format() -> None:
    """The message format must match the expected pattern."""


# =============================================================================
# Tests: Parser.get_formatter_class
# =============================================================================


def test_get_formatter_class_returns_callable() -> None:
    """``get_formatter_class()`` must return a callable."""


def test_get_formatter_class_creates_formatter() -> None:
    """Calling the returned callable with a prog name must produce an ``HelpFormatter`` instance."""


# =============================================================================
# Tests: Parser — argument parsing
# =============================================================================


def test_parse_args_success_returns_namespace() -> None:
    """``parse_args(["value"])`` must return a ``Namespace`` with the argument."""


def test_parse_args_missing_required_raises_parser_error() -> None:
    """``parse_args([])`` for a required positional argument must raise ``ParserError``."""


def test_parse_known_args_returns_extras() -> None:
    """``parse_known_args(["val", "extra"])`` must return ``(namespace, ["extra"])``."""


# =============================================================================
# Tests: Parser vs standard argparse — error handling differences
# =============================================================================


def test_does_not_call_sys_exit_on_error() -> None:
    """Unlike ``argparse.ArgumentParser``, ``Parser.error`` must *never* call ``sys.exit``."""


def test_does_not_print_usage_to_stderr() -> None:
    """``error()`` must not print usage text to ``stderr``."""


# =============================================================================
# Tests: Integration with parse_command_arguments
# =============================================================================


def test_parser_used_by_parse_command_arguments() -> None:
    """``parse_command_arguments`` must use ``Parser`` so failures raise ``ParserError``."""
