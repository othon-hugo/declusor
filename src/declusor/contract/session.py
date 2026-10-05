from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .command import ICommand
    from .connection import IConnection
    from .input_source import IInputSource
    from .plugin import IPluginProcessor
    from .router import IRouter
    from .view import IView


class SessionContext:
    """Encapsulates the active client session and coordinates command execution.

    Provides access to the transport connection, operator view, optional input
    source, and plugin processor, while offering ``execute(command)`` to run
    commands within this session.
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
            plugin_processor: Plugin processor for resolving client assets and payloads.
            input_source: Optional input source for operator command and raw input.
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
    def plugin(self) -> "IPluginProcessor":
        """Client plugin processor for asset resolution and payload loading."""

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
            session: Active session context holding the connection, view, plugin processor, and optional input source.
            router: Router resolving command routes to controllers.
        """

        raise NotImplementedError
