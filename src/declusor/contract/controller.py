from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from declusor import util

if TYPE_CHECKING:
    from declusor.contract.client import IClientFileStore
    from declusor.contract.command import ICommand
    from declusor.contract.connection import IConnection
    from declusor.contract.console import IConsole


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

    Provides access to the transport connection, operator console, and file store,
    while offering an ``execute(command)`` method to run commands within this session.
    """

    def __init__(
        self,
        connection: "IConnection",
        console: "IConsole",
        files: "IClientFileStore",
    ) -> None:
        """Initialize the active session context.

        Args:
            connection: Active connection to the remote client.
            console: Console interface for operator input/output.
            files: Client file store for module/library loading.
        """
        self._connection = connection
        self._console = console
        self._files = files

    @property
    def connection(self) -> "IConnection":
        """Active connection to the remote client."""

        return self._connection

    @property
    def console(self) -> "IConsole":
        """Console interface for operator I/O."""

        return self._console

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

    def __getitem__(self, index: int) -> Any:
        """Allow tuple indexing for backward compatibility."""

        items = (self._connection, self._console, self._files)

        return items[index]

    def __iter__(self) -> Iterator[Any]:
        """Allow tuple unpacking (connection, console, files) for backward compatibility."""

        return iter((self._connection, self._console, self._files))

    def __len__(self) -> int:
        """Return 3 for tuple compatibility."""

        return 3


ControllerDependencies = SessionContext
"""Backward compatibility alias for SessionContext."""


class ControllerRequest(str):
    """Encapsulates raw command line request text with parsing utilities."""

    def parse_arguments(
        self,
        definitions: util.ArgumentDefinitions,
        allow_unknown: bool = False,
    ) -> tuple[util.ParsedArguments, list[str]]:
        return util.parse_command_arguments(self, definitions, allow_unknown=allow_unknown)


Controller = Callable[[SessionContext, ControllerRequest], ControllerResult | None]
"""Type alias for a controller function.

A controller receives an active session context and the command request from the
presentation loop. It optionally returns a ControllerResult to signal lifecycle
actions (e.g. TERMINATE).
"""
