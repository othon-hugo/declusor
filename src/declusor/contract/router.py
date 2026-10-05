from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from declusor.contract.controller import Controller


@dataclass(frozen=True)
class RouteHelp:
    """Short and detailed help text associated with a route."""

    short: str = ""
    complement: str = ""


@dataclass(frozen=True)
class RouteRegistration:
    """Controller and route-owned help metadata registered together."""

    controller: "Controller"
    help: RouteHelp


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
