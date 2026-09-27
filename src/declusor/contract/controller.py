from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .session import SessionContext

ArgumentDefinitions = Mapping[str, type]
"""Mapping of argument names to expected argument types."""

ParsedArguments = dict[str, str | int | float | bool]
"""Extracted argument-value pairs resulting from parsing."""

Controller = Callable[["SessionContext", "ControllerRequest"], "ControllerResult"]
"""Type alias for a controller function.

A controller receives an active session context and the command request from the
presentation loop. It optionally returns a ControllerResult to signal lifecycle
actions (e.g. TERMINATE).
"""


class ControllerAction(StrEnum):
    """Lifecycle actions signaled by controllers to the presentation layer."""

    CONTINUE = "CONTINUE"
    """[...]"""

    TERMINATE = "TERMINATE"
    """[...]"""


@dataclass(frozen=True)
class ControllerResult:
    """Result returned by a controller to the presentation layer."""

    action: ControllerAction = ControllerAction.CONTINUE
    message: str | None = None


@dataclass(frozen=True)
class ControllerRequest(ABC):
    """Encapsulates raw command line request text with parsing utilities."""

    request_line: str = ""

    @abstractmethod
    def parse_arguments(
        self,
        definitions: ArgumentDefinitions,
        allow_unknown: bool = False,
    ) -> tuple[ParsedArguments, list[str]]:
        """[...]"""

        raise NotImplementedError
