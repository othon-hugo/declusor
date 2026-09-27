from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from declusor.contract.command import ICommand
    from declusor.contract.connection import IConnection
    from declusor.contract.input_source import IInputSource
    from declusor.contract.plugin import IPluginProcessor
    from declusor.contract.router import IRouter
    from declusor.contract.view import IView


class SessionContext:
    """Encapsulates the active client session and coordinates command execution.

    Provides access to the transport connection, operator view, input source, and file store,
    while offering an ``execute(command)`` method to run commands within this session.
    """

    def __init__(
        self,
        connection: "IConnection",
        view: "IView",
        plugin_processor: "IPluginProcessor",
        input_source: "IInputSource | None" = None,
    ) -> None:
        """Initialize the active session context.

        Args:
            connection: Active connection to the remote client.
            view: View interface for operator output presentation.
            input: Optional input source interface for operator command/input reading.
            files: Client file store for module/library loading.
        """

        self._connection = connection
        self._view = view
        self._plugin_processor = plugin_processor
        self._input_source = input_source

    @property
    def connection(self) -> "IConnection":
        """Active connection to the remote client."""

        return self._connection

    @property
    def view(self) -> "IView":
        """View interface for operator output presentation."""

        return self._view

    @property
    def input(self) -> "IInputSource | None":
        """Optional input source interface for operator command/input reading."""

        return self._input_source

    @property
    def files(self) -> "IPluginProcessor":
        """Client file store for module/library loading."""

        return self._plugin_processor

    def execute(self, command: "ICommand") -> None:
        """Execute a command within this session context.

        Args:
            command: The command object to execute.
        """

        command.execute(self)


class ISessionRunner(ABC):
    """Contract for executing a workflow or interaction loop over an active session."""

    @abstractmethod
    def run(self, session: "SessionContext", router: "IRouter", /) -> None:
        """Execute the workflow on *session* using *router*.

        Args:
            session: Active session context holding connection, view, input, and files.
            router: Router resolving command routes to controllers.
        """

        raise NotImplementedError
