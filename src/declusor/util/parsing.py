import shlex
import types
from argparse import ArgumentParser, HelpFormatter
from collections.abc import Callable, Mapping
from typing import Any, NoReturn, TypeAlias, Union, get_args, get_origin

from declusor import config

union_types = (Union, types.UnionType)

SupportedType: TypeAlias = type[str] | type[int]
"""Primitive types accepted as command-line arguments."""

ArgumentType: TypeAlias = SupportedType | types.UnionType | Any
"""Type specification for a command argument, including optional forms."""

ArgumentDefinitions: TypeAlias = Mapping[str, ArgumentType]
"""Mapping of argument names to their expected types."""

ParsedArguments: TypeAlias = dict[str, Any]
"""Extracted argument-value pairs resulting from parsing."""


class Parser(ArgumentParser):
    """Custom argument parser that extends argparse.ArgumentParser."""

    def __init__(self, /, prog: str | None = None, usage: str | None = None, description: str | None = None, add_help: bool = True) -> None:
        formatter_class = self.get_formatter_class()

        super().__init__(
            prog=prog,
            usage=usage,
            description=description,
            formatter_class=formatter_class,
            add_help=add_help,
        )

    def error(self, message: str) -> NoReturn:
        """Overrides the default ArgumentParser error behavior."""

        raise config.ParserError(message)

    def get_formatter_class(self) -> Callable[..., HelpFormatter]:
        """Subclasses can override this to customize help formatting."""

        return self._default_formatter_factory

    @staticmethod
    def _default_formatter_factory(*, prog: str) -> HelpFormatter:
        return HelpFormatter(prog, max_help_position=30)


def build_command_parser(definitions: ArgumentDefinitions) -> Parser:
    """Builds and configures a command parser based on argument definitions.

    Args:
        definitions: A mapping of argument names to their expected types.

    Returns:
        A configured Parser instance ready to process input arguments.

    Raises:
        InvalidOperation: If an argument type is not supported.
    """

    supported_types: set[SupportedType] = {str, int}
    parser: Parser = Parser(add_help=False)

    for arg_name, raw_type in definitions.items():
        origin: Any = get_origin(raw_type)
        is_optional: bool = False
        target_type: Any = raw_type

        if origin in union_types:
            all_args: tuple[Any, ...] = get_args(raw_type)
            non_none_args: list[Any] = [a for a in all_args if a is not type(None)]

            if len(non_none_args) < len(all_args):
                is_optional = True

            if len(non_none_args) == 1:
                target_type = non_none_args[0]

        if target_type not in supported_types:
            raise config.InvalidOperation(f"Argument type {target_type!r} for {arg_name!r} is not supported.")

        kwargs: dict[str, Any] = {"type": target_type}

        if is_optional:
            kwargs["nargs"] = "?"
            kwargs["default"] = None

        parser.add_argument(arg_name, **kwargs)

    return parser


def parse_command_arguments(line: str, definitions: ArgumentDefinitions, allow_unknown: bool = False) -> tuple[ParsedArguments, list[str]]:
    """Parses command arguments from a string based on provided definitions.

    Args:
        line: The command line string to parse.
        definitions: A mapping of argument names to their expected types (str or int).
        allow_unknown: If True, unknown arguments are returned instead of raising an error.

    Returns:
        A tuple containing:
            - dict of parsed arguments
            - list of unknown arguments (if allow_unknown=True)

    Raises:
        InvalidOperation: If an argument type is not supported or if there is a parsing error.
    """

    cleaned_line: str = line.strip()

    if not cleaned_line:
        return {}, []

    parser: Parser = build_command_parser(definitions)

    try:
        args_list: list[str] = shlex.split(cleaned_line)
    except ValueError as e:
        raise config.InvalidOperation(f"Parsing error: {e}") from e

    unrecognized_args: list[str]

    if allow_unknown:
        namespace, unrecognized_args = parser.parse_known_args(args_list)
    else:
        namespace = parser.parse_args(args_list)
        unrecognized_args = []

    return vars(namespace), unrecognized_args
