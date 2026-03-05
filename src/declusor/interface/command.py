from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from declusor.interface.connection import IConnection
    from declusor.interface.console import IConsole


class ICommand(ABC):
    """Abstract base class defining the command interface.

    Commands encapsulate executable actions that can be performed
    within a session context.
    """

    @abstractmethod
    def execute(self, session: "IConnection", console: "IConsole", /) -> None:
        """Execute the command in the given session.

        Args:
            session: The session context in which to execute the command.
        """

        raise NotImplementedError
