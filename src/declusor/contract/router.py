from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from declusor.contract.controller import Controller


class IRouter(ABC):
    """Maps command names to their controller functions.

    Manages route registration (``connect``) and dispatch (``locate``),
    and provides human-readable documentation for all registered routes.
    """

    @property
    @abstractmethod
    def routes(self) -> tuple[str, ...]:
        """All currently registered route names.

        Returns:
            A tuple of route name strings in registration order.
        """

        raise NotImplementedError

    @abstractmethod
    def get_route_usage(self, route: str, /) -> str:
        """Return the one-line usage description for a registered route.

        Args:
            route: The route name to look up.

        Returns:
            The first line of the controller's docstring, or an empty string
            if no documentation is available.
        """

        raise NotImplementedError

    @abstractmethod
    def connect(self, route: str, controller: "Controller", /) -> None:
        """Register a controller under a route name.

        Args:
            route: The command name to register (leading/trailing whitespace
                is stripped automatically).
            controller: The ``Controller`` callable to associate with *route*.

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
