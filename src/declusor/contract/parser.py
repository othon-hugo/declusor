from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TypedDict


class ParsedArguments(TypedDict):
    """Base TypedDict for plugin-specific parsed options.

    Autonomous plugins subclass this to declare their statically typed options.
    Parsers never construct this directly — plugins do via ``extract_options()``.
    """


class IArgumentParser[T: ParsedArguments](ABC):
    """Generic contract for a command-line argument parser.

    Type parameter ``T`` is the typed result produced by ``parse()``,
    e.g. a ``TypedDict`` subclass holding the validated CLI values for a
    specific plugin.
    """

    @abstractmethod
    def add_argument(self, *name_or_flags: str, **kwargs: object) -> None:
        """Register a command-line argument or option.

        Args:
            *name_or_flags: One positional name or one or more option flags
                (e.g. ``\"host\"`` or ``\"-p\"``, ``\"--plugin\"``).
            **kwargs: Forwarded verbatim to the underlying parser implementation
                (e.g. ``type``, ``default``, ``help``, ``nargs``).
        """

        raise NotImplementedError

    @abstractmethod
    def parse(self, argv: Sequence[str] | None = None, /) -> T:
        """Parse command-line arguments and return a typed result.

        Args:
            argv: Optional sequence of arguments to parse, excluding the program
                name. Reads from ``sys.argv[1:]`` when ``None``.

        Returns:
            A fully validated instance of ``T`` populated from arguments.

        Raises:
            ParserError: If required arguments are missing or values are invalid.
        """

        raise NotImplementedError
