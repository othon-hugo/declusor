"""Tests for the ``declusor.util.parsing`` module."""

import pytest

from declusor import config
from declusor.util import parsing


# =============================================================================
# Tests: parsing.Parser.error (Custom parser error handling)
# =============================================================================

def test_parser_error_raises_parser_error() -> None:
    """Invoking the parser error handler must raise a configured ``ParserError``."""

    # ARRANGE: Create an instance of the custom argument parser
    parser = parsing.Parser(prog="test")

    # ACT & ASSERT: Inducing a parser constraint hit propagates as the unified error wrapper
    with pytest.raises(config.ParserError, match="invalid argument context"):
        parser.error("invalid argument context")


# =============================================================================
# Tests: parsing.parse_command_arguments (Command line parsing)
# =============================================================================

def test_parse_command_arguments_returns_parsed_dict() -> None:
    """Parsing valid command arguments must return a dictionary of parsed values mapped to their definitions."""

    # ARRANGE: Set up explicit schemas with str and int mapped variants
    definitions: parsing.ArgumentDefinitions = {"host": str, "port": int}
    cmd_line = "127.0.0.1 8080"

    # ACT: Evaluate the command mapping extraction
    parsed, unrecognized = parsing.parse_command_arguments(cmd_line, definitions)

    # ASSERT: Should neatly correlate the sequence and ignore unknowns
    assert parsed == {"host": "127.0.0.1", "port": 8080}
    assert unrecognized == []

def test_parse_command_arguments_with_empty_input_and_no_definition_succeeds() -> None:
    """Parsing an empty command string with no argument definitions must immediately return an empty result."""

    # ARRANGE: No definitions, empty string
    definitions: parsing.ArgumentDefinitions = {}
    cmd_line = "   "

    # ACT: Run evaluation
    parsed, unrecognized = parsing.parse_command_arguments(cmd_line, definitions)

    # ASSERT: Processing shortcuts early
    assert parsed == {}
    assert unrecognized == []

def test_parse_command_arguments_with_unknown_args_allowed_returns_unrecognized() -> None:
    """Parsing arguments with unknown ones allowed must return the recognized terms and a list of unrecognized ones."""

    # ARRANGE: Provide base schema and extra flag inputs
    definitions: parsing.ArgumentDefinitions = {"address": str}
    cmd_line = "localhost --verbose --timeout=5"

    # ACT: Evaluate in relaxed parsing mode
    parsed, unrecognized = parsing.parse_command_arguments(cmd_line, definitions, allow_unknown=True)

    # ASSERT: Core terms parsed, leftover sequence appended cleanly
    assert parsed == {"address": "localhost"}
    assert unrecognized == ["--verbose", "--timeout=5"]

def test_parse_command_arguments_raises_invalid_operation_on_unsupported_type() -> None:
    """Parsing command arguments with unsupported definition types must raise an ``InvalidOperation`` error."""

    # ARRANGE: Prepare schema with arbitrary non-supported type mapping (e.g. bytes/list)
    definitions: parsing.ArgumentDefinitions = {"blob": bytes}  # type: ignore
    cmd_line = "testdata"

    # ACT & ASSERT: Expected failure during schema evaluation wrapper
    with pytest.raises(config.InvalidOperation, match="Argument type <class 'bytes'> for 'blob' is not supported."):
        parsing.parse_command_arguments(cmd_line, definitions)

def test_parse_command_arguments_raises_invalid_operation_on_shlex_error() -> None:
    """Parsing a malformed command string must raise an ``InvalidOperation`` error."""

    # ARRANGE: Inject syntactically invalid quoting
    definitions: parsing.ArgumentDefinitions = {"message": str}
    cmd_line = "unclosed 'quote string"

    # ACT & ASSERT: Check if shlex splits safely bubble back up with our standard exception
    with pytest.raises(config.InvalidOperation, match="Parsing error"):
        parsing.parse_command_arguments(cmd_line, definitions)

def test_parse_command_arguments_supports_optional_unions() -> None:
    """Parsing definition types consisting of optional unions must be handled cleanly via optional syntax modifiers."""

    # ARRANGE: Python union hint translating to optional nargs="?"
    from typing import Union

    definitions: parsing.ArgumentDefinitions = {"domain": str, "weight": Union[int, None]}

    # ACT: Run without the optional parameter
    parsed, _ = parsing.parse_command_arguments("example.com", definitions)

    # ASSERT: The missing value cleanly falls back to None instead of syntax errors
    assert parsed == {"domain": "example.com", "weight": None}


# =============================================================================
# Bug Regression Tests
# =============================================================================

def test_regression_parse_command_arguments_supports_pep604_optional_unions() -> None:
    """Regression test for PEP 604 union types inside `parsing.py` breaking."""

    # ARRANGE: Define definition type that previously broke logic (TypeError due to `types.UnionType`)
    definitions: parsing.ArgumentDefinitions = {"domain": str, "weight": int | None}

    # ACT: Evaluate using the new modern Python syntactical union definitions
    parsed, _ = parsing.parse_command_arguments("example.com", definitions)

    # ASSERT: Value is effectively bypassed
    assert parsed == {"domain": "example.com", "weight": None}
