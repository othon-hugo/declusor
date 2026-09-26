from declusor import config, contract


class DummyRouter(contract.IRouter):
    """Fully-typed router supporting deterministic route registration and dispatch."""

    def __init__(self) -> None:
        self._routes: dict[str, contract.Controller] = {}
        self._usage: dict[str, str] = {}
        self.locate_calls: list[str] = []

    @property
    def routes(self) -> tuple[str, ...]:
        return tuple(self._routes.keys())

    def get_route_usage(self, route: str, /) -> str:
        r = route.strip()

        if r in self._usage:
            return self._usage[r]

        if r in self._routes:
            doc = getattr(self._routes[r], "__doc__", None)

            if isinstance(doc, str) and doc.strip():
                return str(doc.strip().splitlines()[0])

        return ""

    def set_route_usage(self, route: str, usage: str) -> None:
        """Override the usage string for a specific route."""

        self._usage[route.strip()] = usage

    def connect(self, route: str, controller: contract.Controller, /) -> None:
        r = route.strip()

        if r in self._routes:
            raise ValueError(f"route already exists: {r}")

        self._routes[r] = controller

    def locate(self, route: str, /) -> contract.Controller:
        r = route.strip()
        self.locate_calls.append(r)

        if r not in self._routes:
            raise config.RouterError(r, "unknown route")

        return self._routes[r]
