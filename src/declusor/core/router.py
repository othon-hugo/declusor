from declusor import config, contract


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

    def completion_mode(self, route: str, /) -> config.RouteCompletionMode:
        """Return the argument completion mode registered for *route*."""

        return self._locate_registration(route).completion_mode

    def connect(
        self,
        route: str,
        registration: contract.RouteRegistration,
        /,
    ) -> None:
        """Register *registration* under *route*.

        Raises:
            DuplicateRouteError: If *route* is already registered.
        """

        route = route.strip()

        if route in self._route_table:
            raise config.DuplicateRouteError(route, "route already exists.")

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

        raise config.RouterError(route)
