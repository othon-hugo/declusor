import pytest

from declusor import config
from declusor.util import parsing


def test_parser_custom_error_raises_parser_error() -> None:
    """Verify Parser.error raises config.ParserError instead of sys.exit."""

    parser = parsing.Parser(prog="test")
    parser.add_argument("name", type=str)

    with pytest.raises(config.ParserError):
        parser.parse_args([])


def test_build_command_parser_with_supported_types() -> None:
    """Verify build_command_parser creates positional arguments correctly."""

    definitions = {
        "command": str,
        "count": int,
        "optional_name": str | None,
    }
    parser = parsing.build_command_parser(definitions)
    args = parser.parse_args(["ls", "5"])

    assert args.command == "ls"
    assert args.count == 5
    assert args.optional_name is None


def test_build_command_parser_with_unsupported_type() -> None:
    """Verify build_command_parser raises InvalidOperation on unsupported types."""

    with pytest.raises(config.InvalidOperation, match="is not supported"):
        parsing.build_command_parser({"bad": list})


def test_parse_command_arguments_success() -> None:
    """Verify parse_command_arguments extracts values into dictionary."""

    definitions = {
        "host": str,
        "port": int,
    }
    parsed, unknown = parsing.parse_command_arguments("127.0.0.1 4444", definitions)

    assert parsed == {"host": "127.0.0.1", "port": 4444}
    assert unknown == []


def test_parse_command_arguments_unknown_args() -> None:
    """Verify parse_command_arguments preserves unknown arguments when allowed."""

    definitions = {"host": str}
    parsed, unknown = parsing.parse_command_arguments("127.0.0.1 extra1 extra2", definitions, allow_unknown=True)

    assert parsed == {"host": "127.0.0.1"}
    assert unknown == ["extra1", "extra2"]


def test_parse_command_arguments_failure() -> None:
    """Verify parse_command_arguments raises ParserError on invalid arguments."""

    definitions = {"port": int}
    with pytest.raises(config.ParserError):
        parsing.parse_command_arguments("not_an_int", definitions)
