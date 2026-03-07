from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from declusor.config import OperationCode


class IProfile(ABC):
    """Client configuration profile.

    Holds connection parameters and protocol configuration.
    Does NOT perform I/O — that's the responsibility of the connection.
    """

    @property
    @abstractmethod
    def bufsize(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def timeout(self) -> float | None:
        raise NotImplementedError

    @abstractmethod
    def format_operation_script(self, opcode: "OperationCode", /, *args: str) -> str | None:
        """Format an operation into a shell command string.

        This is pure string formatting — no I/O.
        """

        raise NotImplementedError

    @abstractmethod
    def format_client_script(self, host: str, port: int, /) -> str:
        raise NotImplementedError
