from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any, TypeAlias

if TYPE_CHECKING:
    from declusor.contract.command import ICommand
    from declusor.contract.connection import IConnection
    from declusor.contract.input_source import IInputSource
    from declusor.contract.plugin import IClientFileStore
    from declusor.contract.view import IView

ArgumentDefinitions: TypeAlias = Mapping[str, Any]
"""Mapping of argument names to expected argument types."""

ParsedArguments: TypeAlias = dict[str, Any]
"""Extracted argument-value pairs resulting from parsing."""


class ControllerAction(StrEnum):
    """Lifecycle actions signaled by controllers to the presentation layer."""

    CONTINUE = "CONTINUE"
    TERMINATE = "TERMINATE"


@dataclass(frozen=True)
class ControllerResult:
    """Result returned by a controller to the presentation layer."""

    action: ControllerAction = ControllerAction.CONTINUE
    message: str | None = None


class SessionContext:
    """Encapsulates the active client session and coordinates command execution.

    Provides access to the transport connection, operator view, input source, and file store,
    while offering an ``execute(command)`` method to run commands within this session.
    """

    def __init__(
        self,
        connection: "IConnection",
        view: "IView",
        input: "IInputSource | None",
        files: "IClientFileStore",
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
        self._input = input
        self._files = files

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

        return self._input

    @property
    def files(self) -> "IClientFileStore":
        """Client file store for module/library loading."""

        return self._files

    def execute(self, command: "ICommand") -> None:
        """Execute a command within this session context.

        Args:
            command: The command object to execute.
        """

        command.execute(self)


@dataclass(frozen=True)
class ControllerRequest:
    """Encapsulates raw command line request text with parsing utilities."""

    request_line: str = ""

    def parse_arguments(
        self,
        definitions: ArgumentDefinitions,
        allow_unknown: bool = False,
    ) -> tuple[ParsedArguments, list[str]]:
        from declusor.util.parsing import parse_command_arguments

        return parse_command_arguments(
            line=self.request_line,
            definitions=definitions,
            allow_unknown=allow_unknown,
        )


Controller = Callable[[SessionContext, ControllerRequest], ControllerResult | None]
"""Type alias for a controller function.

A controller receives an active session context and the command request from the
presentation loop. It optionally returns a ControllerResult to signal lifecycle
actions (e.g. TERMINATE).
"""
