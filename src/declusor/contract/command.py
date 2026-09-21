from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from declusor.contract.client import IClientFileStore
    from declusor.contract.connection import IConnection
    from declusor.contract.console import IConsole


class ICommand(ABC):
    """An executable operation that runs within an active connection context.

    Each command encapsulates the data and behavior required to perform a
    single remote operation, such as executing a file, uploading a payload,
    or running a shell command.

    Commands do not own or retain the connection or console they operate on.
    These dependencies are provided by the caller for each execution.
    """

    def __init__(self, connection: "IConnection", console: "IConsole", /, files: "IClientFileStore | None" = None) -> None:
        """[...]

        Args:
            connection: [...]
            console: [...]
            files: [...]
        """

        super().__init__()

        self._connection = connection
        self._console = console

        if files is not None:
            self._files = files

    @abstractmethod
    def send_request(self) -> None:
        """Send the request that initiates the remote operation.

        Implementations are responsible for transmitting the command request
        through the active connection. This method does not read or process
        the response produced by the operation.
        """

        raise NotImplementedError

    @abstractmethod
    def read_response(self) -> None:
        """Read and display the response produced by the remote operation.

        Implementations are responsible for consuming the response through
        the active connection and presenting its output through the console.
        """

        raise NotImplementedError

    def execute(self) -> None:
        """Execute the complete request-response lifecycle.

        Sends the command request and then reads and displays the response.
        Subclasses may override this method when the operation requires a
        different execution sequence.
        """

        self.read_response()
        self.send_request()
