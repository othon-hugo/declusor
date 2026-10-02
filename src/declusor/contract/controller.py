from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
    from .session import SessionContext

ArgumentDefinitions = Mapping[str, type | object]
"""Mapping of argument names to expected argument types."""


class ControllerArguments(TypedDict):
    """Base TypedDict for parsed controller arguments.

    Controllers subclass this to declare statically typed argument definitions.
    """


class IControllerRequest[T: ControllerArguments](ABC):
    """Encapsulates raw command line request text with parsing utilities.

    Autonomous controllers declare their specific arguments TypedDict subclassing
    ``ControllerArguments`` and specify it as the type argument ``T`` on
    ``IControllerRequest[T]``.
    """

    @property
    @abstractmethod
    def request_line(self) -> str:
        """The raw command line text of the request."""

        raise NotImplementedError

    @abstractmethod
    def parse_arguments(
        self,
        definitions: ArgumentDefinitions,
        allow_unknown: bool = False,
    ) -> tuple[T, list[str]]:
        """Parse command-line arguments using provided definitions.

        Args:
            definitions: Schema defining expected argument names and types.
            allow_unknown: Whether to permit unrecognized trailing arguments.

        Returns:
            Tuple of the parsed arguments instance ``T`` and any unknown tokens.
        """

        raise NotImplementedError


Controller = Callable[["SessionContext", IControllerRequest[Any]], "ControllerResult"]
"""Type alias for a controller function.

A controller receives an active session context and the command request from the
presentation loop. It optionally returns a ControllerResult to signal lifecycle
actions (e.g. TERMINATE).
"""


class ControllerAction(StrEnum):
    """Lifecycle actions signaled by controllers to the presentation layer."""

    CONTINUE = "CONTINUE"
    """Signal the presentation loop to continue prompting the user for commands."""

    TERMINATE = "TERMINATE"
    """Signal the presentation loop to terminate the interactive session gracefully."""


@dataclass(frozen=True)
class ControllerResult:
    """Result returned by a controller to the presentation layer."""

    action: ControllerAction = ControllerAction.CONTINUE
    """Lifecycle action indicating whether to continue or terminate the session."""

    message: str | None = None
    """Optional informational message to be displayed by the presentation layer."""

    @classmethod
    def for_continuation(cls, message: str | None = None) -> "ControllerResult":
        """Create a result signaling the presentation loop to continue.

        Args:
            message: Optional informational message to display to the user.

        Returns:
            A frozen ``ControllerResult`` with ``ControllerAction.CONTINUE``.
        """

        return cls(action=ControllerAction.CONTINUE, message=message)

    @classmethod
    def for_termination(cls, message: str | None = None) -> "ControllerResult":
        """Create a result signaling the presentation loop to terminate.

        Args:
            message: Optional message to display to the user before termination.

        Returns:
            A frozen ``ControllerResult`` with ``ControllerAction.TERMINATE``.
        """

        return cls(action=ControllerAction.TERMINATE, message=message)
