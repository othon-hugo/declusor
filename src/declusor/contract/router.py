"""Command routing contracts, route metadata definitions, and completion mode specifications."""

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from declusor import config

if TYPE_CHECKING:
    from .controller import Controller


@dataclass(frozen=True)
class RouteHelp:
    """Short and detailed help text associated with a route."""

    short: str = ""
    """Brief single-line summary of route purpose shown in help listings."""

    complement: str = ""
    """Extended usage syntax and argument instructions shown in route details."""


@dataclass(frozen=True)
class RouteRegistration:
    """Controller, route-owned help metadata, and argument completion semantics."""

    controller: "Controller"
    """Controller function handling requests directed to this route."""

    help: RouteHelp = field(default_factory=RouteHelp)
    """Structured documentation and usage metadata for this route."""

    completion_mode: config.RouteCompletionMode = config.RouteCompletionMode.NONE
    """Argument autocompletion policy enforced during terminal input."""


RouteTable = Mapping[str, RouteRegistration]
"""Mapping of open-ended route names to their registrations."""


class IRouter(ABC):
    """Maps command names to their controller functions.

    Manages route registration (``connect``), dispatch (``locate``), and
    route-specific help metadata.
    """

    @property
    @abstractmethod
    def routes(self) -> Sequence[str]:
        """All currently registered route names.

        Returns:
            A tuple of route name strings in registration order.
        """

        raise NotImplementedError

    @abstractmethod
    def help(self, route: str, /) -> RouteHelp:
        """Return the help metadata registered for a route.

        Args:
            route: The route name to look up.

        Returns:
            The route's short and detailed help text.
        """

        raise NotImplementedError

    @abstractmethod
    def completion_mode(self, route: str, /) -> config.RouteCompletionMode:
        """Return the argument completion mode registered for a route.

        Args:
            route: The route name to look up.

        Returns:
            The route's RouteCompletionMode.
        """

        raise NotImplementedError

    @abstractmethod
    def connect(self, route: str, registration: RouteRegistration, /) -> None:
        """Register a controller and its help metadata under a route name.

        Args:
            route: The command name to register (leading/trailing whitespace
                is stripped automatically).
            registration: The controller and route-specific help to associate
                with *route*.

        Raises:
            ValueError: If *route* is already registered.
        """

        raise NotImplementedError

    @abstractmethod
    def locate(self, route: str, /) -> "Controller":
        """Return the controller registered under *route*.

        Args:
            route: The command name to look up.

        Returns:
            The ``Controller`` callable bound to *route*.

        Raises:
            RouterError: If *route* is not registered.
        """

        raise NotImplementedError
