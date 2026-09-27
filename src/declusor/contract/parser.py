from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TypedDict


class ParsedArguments(TypedDict):
    """[...]"""


class IArgumentParser[T: ParsedArguments](ABC):
    """Generic contract for a command-line argument parser.

    Type parameter ``T`` is the typed result produced by ``parse()``
    (e.g. a ``TypedDict`` holding the validated CLI values).
    """

    @abstractmethod
    def add_argument(self, name: str, *flags: str) -> None:
        """Register a command-line argument or option.

        [...]
        """

        raise NotImplementedError

    @abstractmethod
    def parse(self, argv: Sequence[str] | None = None, /) -> T:
        """Parse command-line arguments and return a typed result.

        Args:
            manager: Plugin manager containing available client plugins.
            argv: Optional sequence of arguments to parse, excluding the program name.

        Returns:
            A fully validated instance of ``T`` populated from arguments.

        Raises:
            ParserError: If required arguments are missing or values are invalid.
        """

        raise NotImplementedError
