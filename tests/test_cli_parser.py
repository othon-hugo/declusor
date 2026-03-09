"""Tests for the ``declusor.cli.parser`` module."""

import sys

import pytest

from declusor import config
from declusor.cli import parser


# =============================================================================
# Tests: DeclusorParser.parse (Argument parsing)
# =============================================================================

def test_declusorparser_parse_returns_valid_options() -> None:
    """Parsing valid command line arguments must return a correctly populated ``DeclusorOptions`` dict."""

    # ARRANGE: Set up a parser instance and simulate sys.argv injection
    declusor_parser = parser.DeclusorParser()

    # ACT: Parse execution sequence
    result = declusor_parser.parse(["localhost", "8080", "--client", "shell_socket.sh"])

    # ASSERT: Arguments conform identically to provided structure
    assert result["host"] == "localhost"
    assert result["port"] == 8080
    assert result["client"] == config.ClientFile.SHELL_SOCKET

def test_declusorparser_parse_uses_default_client_if_missing() -> None:
    """Parsing arguments without specifying a client must default to shell_socket.sh."""

    # ARRANGE: Provide only mandatory tokens
    declusor_parser = parser.DeclusorParser()

    # ACT: Parse sequence bypassing standard optional
    result = declusor_parser.parse(["127.0.0.1", "9090"])

    # ASSERT: Internal framework injects default
    assert result["client"] == config.ClientFile.SHELL_SOCKET

def test_declusorparser_parse_raises_parser_error_on_missing_argument() -> None:
    """Parsing arguments missing required positional parameters must raise a ``ParserError``."""

    # ARRANGE: Missing parameters
    declusor_parser = parser.DeclusorParser()

    # ACT & ASSERT: Missing port aborts operation gracefully with explicit notification
    with pytest.raises(config.ParserError):
        declusor_parser.parse(["127.0.0.1"])

def test_declusorparser_parse_raises_parser_error_on_invalid_client_path() -> None:
    """Invoking internal parameter bounds checks for invalid relative paths logs a parser error."""

    # ARRANGE: Provide dummy framework structure target mapping
    declusor_parser = parser.DeclusorParser()

    # ACT & ASSERT: Suppress and raise unsafe client target mappings proactively
    with pytest.raises(config.ParserError, match="invalid ClientFile value:"):
        declusor_parser.parse(["127.0.0.1", "8080", "--client", "../untrusted.sh"])
