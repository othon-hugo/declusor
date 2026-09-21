from collections.abc import Callable
from typing import TYPE_CHECKING, NamedTuple

from declusor import util

if TYPE_CHECKING:
    from declusor.contract.client import IClientFileStore
    from declusor.contract.connection import IConnection
    from declusor.contract.console import IConsole


class ControllerDependencies(NamedTuple):
    """..."""

    connection: "IConnection"
    console: "IConsole"
    files: "IClientFileStore"


class ControllerRequest(str):
    """..."""

    def parse_arguments(self, definitions: util.ArgumentDefinitions, allow_unknown: bool = False) -> tuple[util.ParsedArguments, list[str]]:
        return util.parse_command_arguments(self, definitions, allow_unknown=allow_unknown)


Controller = Callable[["ControllerDependencies", ControllerRequest], None]
"""Type alias for a controller function.

A controller receives an active connection, a console for operator I/O,
and the raw argument string from the command line.
"""
