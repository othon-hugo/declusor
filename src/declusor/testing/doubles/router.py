"""Deterministic router test double tracking route registrations."""

from declusor import config, contract


class DummyRouter(contract.IRouter):
    """Fully-typed router supporting deterministic route registration and dispatch."""

    def __init__(self) -> None:
        """Initialize in-memory route dictionary and dispatch call tracker."""

        self._routes: dict[str, contract.RouteRegistration] = {}
        self.locate_calls: list[str] = []

    @property
    def routes(self) -> tuple[str, ...]:
        """All currently registered route names."""

        return tuple(self._routes.keys())

    def help(self, route: str, /) -> contract.RouteHelp:
        """Return route-specific help metadata."""

        r = route.strip()
        registration = self._routes.get(r)

        return registration.help if registration is not None else contract.RouteHelp()

    def completion_mode(self, route: str, /) -> config.RouteCompletionMode:
        """Return route completion mode."""

        r = route.strip()
        registration = self._routes.get(r)

        return registration.completion_mode if registration is not None else config.RouteCompletionMode.NONE

    def set_route_help(self, route: str, route_help: contract.RouteHelp) -> None:
        """Override the help metadata for a specific route."""

        r = route.strip()
        if r in self._routes:
            registration = self._routes[r]
            self._routes[r] = contract.RouteRegistration(
                registration.controller,
                route_help,
                registration.completion_mode,
            )

    def connect(self, route: str, registration: contract.RouteRegistration, /) -> None:
        """Register a route with its associated controller and metadata."""

        r = route.strip()

        if r in self._routes:
            raise config.DuplicateRouteError(r, f"route already exists: {r}")

        self._routes[r] = registration

    def locate(self, route: str, /) -> contract.Controller:
        """Locate and return the controller callable registered for route."""

        r = route.strip()
        self.locate_calls.append(r)

        if r not in self._routes:
            raise config.RouterError(r, "unknown route")

        return self._routes[r].controller
