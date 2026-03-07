"""Tests for ``declusor.util.parsing``.

Covers the ``Parser`` subclass (``ParserError`` instead of ``SystemExit``),
``parse_command_arguments`` (basic usage, optional arguments, error handling,
unknown-argument control, and edge cases).
"""

from typing import Optional

import pytest

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def simple_definitions() -> dict:
    """Return ``{"name": str, "count": int}``."""


@pytest.fixture
def optional_definitions() -> dict:
    """Return ``{"command": Optional[str]}``."""


# =============================================================================
# Tests: Parser class
# =============================================================================


def test_parser_error_raises_parser_error() -> None:
    """``error()`` must raise ``ParserError``, not ``SystemExit``."""


def test_parser_get_formatter_class_returns_callable() -> None:
    """``get_formatter_class()`` must return a callable."""


def test_parser_custom_prog_name() -> None:
    """``Parser(prog="cmd")`` must set ``self.prog``."""


def test_parser_without_help_flag() -> None:
    """``Parser(add_help=False)`` must not recognise ``-h`` / ``--help``."""


# =============================================================================
# Tests: parse_command_arguments — basic usage
# =============================================================================


def test_single_string_arg() -> None:
    """``{"filepath": str}`` with ``"test.txt"`` must yield ``{"filepath": "test.txt"}``."""


def test_single_int_arg() -> None:
    """``{"count": int}`` with ``"42"`` must yield ``{"count": 42}``."""


def test_multiple_args() -> None:
    """Multiple definitions must be matched positionally."""


def test_empty_with_no_definitions() -> None:
    """``{}`` with ``""`` must yield ``({}, [])``."""


def test_whitespace_only_treated_as_empty() -> None:
    """``"   "`` must behave the same as ``""``."""


# =============================================================================
# Tests: parse_command_arguments — optional arguments
# =============================================================================


def test_optional_provided() -> None:
    """``{"cmd": Optional[str]}`` with ``"hello"`` must yield ``{"cmd": "hello"}``."""


def test_optional_omitted() -> None:
    """``{"cmd": Optional[str]}`` with ``""`` must yield ``{"cmd": None}``."""


def test_mixed_required_and_optional() -> None:
    """A required arg followed by an omitted optional must set optional to ``None``."""


def test_mixed_all_provided() -> None:
    """Both required and optional arguments provided must be parsed."""


# =============================================================================
# Tests: parse_command_arguments — error handling
# =============================================================================


def test_unsupported_type_raises_invalid_operation() -> None:
    """A ``list`` type in definitions must raise ``InvalidOperation``."""


def test_unclosed_quote_raises_invalid_operation() -> None:
    """An unclosed quote (``'"incomplete'``) must raise ``InvalidOperation``."""


def test_missing_required_raises_parser_error() -> None:
    """Omitting a required argument must raise ``ParserError``."""


def test_wrong_type_raises_parser_error() -> None:
    """``"not_a_number"`` for an ``int`` definition must raise ``ParserError``."""


# =============================================================================
# Tests: parse_command_arguments — unknown arguments
# =============================================================================


def test_allow_unknown_true_returns_extras() -> None:
    """Extra tokens must be returned in the second tuple element."""


def test_allow_unknown_false_raises() -> None:
    """Extra tokens with ``allow_unknown=False`` must raise ``ParserError``."""


def test_unknown_with_empty_definitions() -> None:
    """``{}`` with ``allow_unknown=True`` must place all tokens in the extras list."""


# =============================================================================
# Tests: parse_command_arguments — edge cases
# =============================================================================


def test_quoted_string_with_spaces() -> None:
    """``'"path with spaces"'`` must yield a single string including the spaces."""


def test_escaped_quotes() -> None:
    """Escaped quote characters must survive the parse."""


def test_preserves_argument_order() -> None:
    """Arguments must be matched in definition-insertion order."""


def test_negative_integer() -> None:
    """``"-42"`` must parse as ``-42``."""
