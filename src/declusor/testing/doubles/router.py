from declusor import config, contract


class DummyRouter(contract.IRouter):
    """Fully-typed router supporting deterministic route registration and dispatch."""

    def __init__(self) -> None:
        self._routes: dict[str, contract.RouteRegistration] = {}
        self.locate_calls: list[str] = []

    @property
    def routes(self) -> tuple[str, ...]:
        return tuple(self._routes.keys())

    def help(self, route: str, /) -> contract.RouteHelp:
        r = route.strip()
        registration = self._routes.get(r)

        return registration.help if registration is not None else contract.RouteHelp()

    def set_route_help(self, route: str, route_help: contract.RouteHelp) -> None:
        """Override the help metadata for a specific route."""

        r = route.strip()
        if r in self._routes:
            registration = self._routes[r]
            self._routes[r] = contract.RouteRegistration(registration.controller, route_help)

    def connect(self, route: str, registration: contract.RouteRegistration | contract.Controller, /) -> None:
        r = route.strip()

        if r in self._routes:
            raise config.DuplicateRouteError(r, f"route already exists: {r}")

        if not isinstance(registration, contract.RouteRegistration):
            registration = contract.RouteRegistration(registration, contract.RouteHelp())

        self._routes[r] = registration

    def locate(self, route: str, /) -> contract.Controller:
        r = route.strip()
        self.locate_calls.append(r)

        if r not in self._routes:
            raise config.RouterError(r, "unknown route")

        return self._routes[r].controller
