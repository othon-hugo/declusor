from argparse import HelpFormatter
from typing import Optional, Union

import pytest

from declusor import config
from declusor.util import parsing


class TestParser:
    """Verify Parser subclass error handling and HelpFormatter configuration."""

    def test_parser_error__custom_message__raises_parser_error(self) -> None:
        """Verify Parser.error raises config.ParserError with the exact error message."""

        parser = parsing.Parser(prog="test_prog")

        with pytest.raises(config.ParserError, match="custom error occurred"):
            parser.error("custom error occurred")

    def test_parser_formatter__default_factory__instantiates_help_formatter_with_position(self) -> None:
        """Verify Parser uses HelpFormatter with max_help_position configured to 30."""

        parser = parsing.Parser(prog="custom_prog")
        formatter = parser.formatter_class(prog="custom_prog")

        assert isinstance(formatter, HelpFormatter)
        assert getattr(formatter, "_max_help_position", None) == 30

    def test_parser_init__custom_arguments__configures_parser_properties(self) -> None:
        """Verify Parser accepts and sets custom prog, usage, and description."""

        parser = parsing.Parser(
            prog="declusor_cli",
            usage="declusor_cli [options]",
            description="Declusor command-line interface",
            add_help=False,
        )

        assert parser.prog == "declusor_cli"
        assert parser.usage == "declusor_cli [options]"
        assert parser.description == "Declusor command-line interface"


class TestBuildCommandParser:
    """Verify dynamic argument parser construction from type definitions."""

    def test_build_command_parser__required_str_and_int__adds_positional_arguments(self) -> None:
        """Verify build_command_parser creates required positional arguments for str and int."""

        definitions = {"cmd": str, "count": int}
        parser = parsing.build_command_parser(definitions)
        args = parser.parse_args(["status", "3"])

        assert args.cmd == "status"
        assert args.count == 3

    def test_build_command_parser__optional_union_type__configures_optional_argument(self) -> None:
        """Verify build_command_parser handles Python 3.10+ union syntax (T | None)."""

        definitions = {"name": str | None}
        parser = parsing.build_command_parser(definitions)

        args_provided = parser.parse_args(["custom_name"])
        assert args_provided.name == "custom_name"

        args_omitted = parser.parse_args([])
        assert args_omitted.name is None

    def test_build_command_parser__typing_union_syntax__configures_optional_argument(self) -> None:
        """Verify build_command_parser handles typing.Union and typing.Optional syntax."""

        definitions = {"tag": Optional[str], "flag": Union[int, None]}  # noqa: UP007, UP045
        parser = parsing.build_command_parser(definitions)

        args_omitted = parser.parse_args([])
        assert args_omitted.tag is None
        assert args_omitted.flag is None

        args_provided = parser.parse_args(["v1.0", "42"])
        assert args_provided.tag == "v1.0"
        assert args_provided.flag == 42

    def test_build_command_parser__optional_int__converts_to_int_or_none(self) -> None:
        """Verify optional int argument converts numeric string and defaults to None."""

        definitions = {"timeout": int | None}
        parser = parsing.build_command_parser(definitions)

        assert parser.parse_args(["60"]).timeout == 60
        assert parser.parse_args([]).timeout is None

    def test_build_command_parser__unsupported_primitive_type__raises_invalid_operation(self) -> None:
        """Verify build_command_parser raises InvalidOperation for unsupported types."""

        with pytest.raises(config.InvalidOperation, match=r"Argument type <class 'float'> for 'ratio' is not supported\."):
            parsing.build_command_parser({"ratio": float})

    def test_build_command_parser__unsupported_multi_type_union__raises_invalid_operation(self) -> None:
        """Verify build_command_parser raises InvalidOperation for multi-type unions like int | str."""

        with pytest.raises(config.InvalidOperation, match="is not supported"):
            parsing.build_command_parser({"mixed": int | str})

    def test_build_command_parser__empty_definitions__builds_empty_parser(self) -> None:
        """Verify build_command_parser creates functional parser when definitions are empty."""

        parser = parsing.build_command_parser({})
        args = parser.parse_args([])

        assert vars(args) == {}


class TestParseCommandArguments:
    """Verify parse_command_arguments line tokenization and validation."""

    def test_parse_command_arguments__valid_positional_arguments__returns_parsed_dict(self) -> None:
        """Verify parse_command_arguments extracts positional values into dictionary."""

        definitions = {"host": str, "port": int}
        parsed, unknown = parsing.parse_command_arguments("127.0.0.1 4444", definitions)

        assert parsed == {"host": "127.0.0.1", "port": 4444}
        assert unknown == []

    def test_parse_command_arguments__optional_argument_provided__parses_supplied_value(self) -> None:
        """Verify optional arguments accept and parse explicitly passed values."""

        definitions = {"host": str, "port": int | None}
        parsed, unknown = parsing.parse_command_arguments("10.0.0.1 9000", definitions)

        assert parsed == {"host": "10.0.0.1", "port": 9000}
        assert unknown == []

    def test_parse_command_arguments__optional_argument_omitted__defaults_to_none(self) -> None:
        """Verify optional arguments default to None when omitted."""

        definitions = {"host": str, "port": int | None}
        parsed, unknown = parsing.parse_command_arguments("10.0.0.1", definitions)

        assert parsed == {"host": "10.0.0.1", "port": None}
        assert unknown == []

    def test_parse_command_arguments__empty_line_and_empty_definitions__returns_empty_tuple(self) -> None:
        """Verify empty input with empty definitions returns empty dictionary and list."""

        parsed, unknown = parsing.parse_command_arguments("", {})

        assert parsed == {}
        assert unknown == []

    def test_parse_command_arguments__empty_line_with_required_args__raises_parser_error(self) -> None:
        """Verify empty input raises ParserError when required definitions exist."""

        with pytest.raises(config.ParserError, match="the following arguments are required"):
            parsing.parse_command_arguments("", {"required_arg": str})

    def test_parse_command_arguments__whitespace_only_line_with_optional_args__returns_none_defaults(self) -> None:
        """Verify whitespace-only input returns None defaults when arguments are optional."""

        parsed, unknown = parsing.parse_command_arguments("   \t  ", {"opt": str | None})

        assert parsed == {"opt": None}
        assert unknown == []

    def test_parse_command_arguments__unclosed_quote__raises_controller_error(self) -> None:
        """Verify syntax error in shlex (unclosed quote) raises ControllerError with cause."""

        with pytest.raises(config.ControllerError, match="Parsing error: No closing quotation") as exc_info:
            parsing.parse_command_arguments("host 'unclosed quotation", {"host": str})

        assert isinstance(exc_info.value.__cause__, ValueError)

    def test_parse_command_arguments__quoted_arguments_with_spaces__preserves_embedded_spaces(self) -> None:
        """Verify quoted strings preserve internal whitespace as single argument value."""

        definitions = {"message": str, "count": int}
        parsed, unknown = parsing.parse_command_arguments('"hello world string" 5', definitions)

        assert parsed == {"message": "hello world string", "count": 5}
        assert unknown == []

    def test_parse_command_arguments__extra_arguments_disallowed__raises_parser_error(self) -> None:
        """Verify extra arguments raise ParserError when allow_unknown=False."""

        definitions = {"host": str}

        with pytest.raises(config.ParserError, match="unrecognized arguments"):
            parsing.parse_command_arguments("127.0.0.1 extra_param", definitions, allow_unknown=False)

    def test_parse_command_arguments__extra_arguments_allowed__collects_unrecognized_args(self) -> None:
        """Verify unknown arguments are returned in list when allow_unknown=True."""

        definitions = {"host": str}
        parsed, unknown = parsing.parse_command_arguments("127.0.0.1 --flag value", definitions, allow_unknown=True)

        assert parsed == {"host": "127.0.0.1"}
        assert unknown == ["--flag", "value"]

    def test_parse_command_arguments__invalid_integer_format__raises_parser_error(self) -> None:
        """Verify passing non-integer value to int argument raises ParserError."""

        definitions = {"port": int}

        with pytest.raises(config.ParserError, match="invalid int value"):
            parsing.parse_command_arguments("not_a_number", definitions)

    def test_parse_command_arguments__missing_required_positional_arg__raises_parser_error(self) -> None:
        """Verify omitting a required positional argument raises ParserError."""

        definitions = {"first": str, "second": str}

        with pytest.raises(config.ParserError, match="the following arguments are required: second"):
            parsing.parse_command_arguments("first_only", definitions)
