from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, NamedTuple

from declusor import util

if TYPE_CHECKING:
    from declusor.contract.client import IClientFileStore
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


class ControllerDependencies(NamedTuple):
    """Runtime dependencies provided to each controller invocation."""

    connection: "IConnection"
    console: "IConsole"
    files: "IClientFileStore"


class ControllerRequest(str):
    """Encapsulates raw command line request text with parsing utilities."""

    def parse_arguments(self, definitions: util.ArgumentDefinitions, allow_unknown: bool = False) -> tuple[util.ParsedArguments, list[str]]:
        return util.parse_command_arguments(self, definitions, allow_unknown=allow_unknown)


Controller = Callable[[ControllerDependencies, ControllerRequest], ControllerResult | None]
"""Type alias for a controller function.

A controller receives an active connection, a console for operator I/O,
and the command request from the presentation loop. It optionally returns a
ControllerResult to signal lifecycle actions (e.g. TERMINATE).
"""
