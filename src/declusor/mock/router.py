from declusor import interface


class MockRouter(interface.IRouter):
    """A mock implementation of IRouter for testing."""

    def __init__(self) -> None:
        self._routes: dict[str, "interface.Controller"] = {}
        self.route_usage: dict[str, str] = {}
        self._documentation = ""

    @property
    def routes(self) -> tuple[str, ...]:
        return tuple(self._routes.keys())

    @property
    def documentation(self) -> str:
        return self._documentation

    def get_route_usage(self, route: str, /) -> str:
        return self.route_usage.get(route, "")

    def connect(self, route: str, controller: "interface.Controller", /) -> None:
        self._routes[route] = controller

    def locate(self, route: str, /) -> "interface.Controller":
        return self._routes[route]
