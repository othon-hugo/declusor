from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from declusor.config import OperationCode


class IProfile(ABC):
    """Immutable configuration profile for a remote client.

    Holds protocol parameters (buffer sizes, timeouts, ACK values, supported
    operations) and performs only pure string formatting. All I/O is
    delegated to the ``IConnection`` implementation.
    """

    @property
    @abstractmethod
    def bufsize(self) -> int:
        """Receive buffer size in bytes used for socket reads."""

        raise NotImplementedError

    @property
    @abstractmethod
    def timeout(self) -> float | None:
        """Default socket operation timeout in seconds, or ``None`` for no timeout."""

        raise NotImplementedError

    @abstractmethod
    def format_operation_script(self, opcode: "OperationCode", /, *args: str) -> str | None:
        """Build the shell command string for a given operation code.

        Maps an ``OperationCode`` to its client-side function name and appends
        each argument as a shell-quoted token. Returns ``None`` if the opcode
        is not supported by this profile.

        Args:
            opcode: The operation to invoke on the client.
            *args: Positional string arguments forwarded to the client function.

        Returns:
            A ready-to-send command string, or ``None`` if the opcode is unsupported.
        """

        raise NotImplementedError

    @abstractmethod
    def format_client_script(self, host: str, port: int, /) -> str:
        raise NotImplementedError
