from declusor import contract
from declusor.config import DuplicateRouteError, RouterError


class Router(contract.IRouter):
    """Default ``IRouter`` implementation backed by an in-memory dictionary.

    Routes and their help metadata are registered together via ``connect``;
    ``locate`` returns the controller while ``help`` returns route metadata.
    The route name is stripped of surrounding whitespace before storage.
    Duplicate registration raises ``DuplicateRouteError``; unknown lookup raises
    ``RouterError``.
    """

    def __init__(self) -> None:
        self._route_table: dict[str, contract.RouteRegistration] = {}

    @property
    def routes(self) -> tuple[str, ...]:
        """All currently registered route names, in insertion order."""

        return tuple(self._route_table.keys())

    def help(self, route: str, /) -> contract.RouteHelp:
        """Return the route-specific help metadata."""

        return self._locate_registration(route).help

    def connect(
        self,
        route: str,
        registration: contract.RouteRegistration | contract.Controller,
        /,
    ) -> None:
        """Register *registration* under *route*.

        Raises:
            DuplicateRouteError: If *route* is already registered.
        """

        route = route.strip()

        if route in self._route_table:
            raise DuplicateRouteError(route, "route already exists.")

        if not isinstance(registration, contract.RouteRegistration):
            registration = contract.RouteRegistration(registration, contract.RouteHelp())

        self._route_table[route] = registration

    def locate(self, route: str, /) -> contract.Controller:
        """Return the controller bound to *route*.

        Raises:
            RouterError: If *route* is not registered.
        """

        return self._locate_registration(route).controller

    def _locate_registration(self, route: str, /) -> contract.RouteRegistration:
        """Return the registration bound to *route*."""

        if registration := self._route_table.get(route.strip()):
            return registration

        raise RouterError(route)
