from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class IParser(ABC, Generic[T]):
    """Generic contract for a command-line argument parser.

    Type parameter ``T`` is the typed result produced by ``parse()``
    (e.g. a ``TypedDict`` holding the validated CLI values).
    """

    @abstractmethod
    def parse(self) -> T:
        """Parse command-line arguments and return a typed result.

        Returns:
            A fully validated instance of ``T`` populated from ``sys.argv``.

        Raises:
            ParserError: If required arguments are missing or values are invalid.
        """

        raise NotImplementedError
