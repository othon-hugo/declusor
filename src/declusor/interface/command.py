from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from declusor.interface.connection import IConnection
    from declusor.interface.console import IConsole


class ICommand(ABC):
    """An executable operation that runs within an active session context.

    Follows the Command design pattern: each subclass encapsulates a single
    remote operation (execute a file, upload a payload, run a shell command,
    etc.) along with the data it needs. Commands are stateless with respect
    to the session — they receive it as a parameter rather than storing it.
    """

    @abstractmethod
    def execute(self, connection: "IConnection", console: "IConsole", /) -> None:
        """Run the command over the given connection.

        Args:
            connection: The active connection through which the operation is sent.
            console: Console used for displaying output or prompting the user.
        """

        raise NotImplementedError
