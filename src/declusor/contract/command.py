from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from declusor.contract.controller import SessionContext


class ICommand(ABC):
    """An executable operation that runs within an active session context.

    Each command encapsulates the parameters and data required to perform a
    single remote operation (e.g. executing a file, uploading a payload,
    loading a module, or running a shell command).

    Commands are stateless with respect to the runtime environment: they do
    not own or retain the connection, console, or file store. These dependencies
    are provided via the ``SessionContext`` upon execution.
    """

    @abstractmethod
    def send_request(self, session: "SessionContext", /) -> None:
        """Send the request initiating the remote operation through the session.

        Implementations transmit the command payload through ``session.connection``.

        Args:
            session: Active session context providing connection and view.
        """

        raise NotImplementedError

    @abstractmethod
    def read_response(self, session: "SessionContext", /) -> None:
        """Read and display the operation response through the session view.

        Implementations consume chunks from ``session.connection`` and write
        them to ``session.view``.

        Args:
            session: Active session context providing connection and view.
        """

        raise NotImplementedError

    def execute(self, session: "SessionContext", /) -> None:
        """Execute the complete request-response lifecycle within the session.

        Transmits the command request and subsequently reads and presents
        the response. Subclasses may override this method when an alternative
        coordination pattern (such as bidirectional streaming) is required.

        Args:
            session: Active session context providing connection and view.
        """

        self.send_request(session)
        self.read_response(session)
