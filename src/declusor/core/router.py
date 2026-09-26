from declusor import contract
from declusor.config import RouterError


class Router(contract.IRouter):
    """Default ``IRouter`` implementation backed by an in-memory dictionary.

    Routes are registered via ``connect`` and dispatched via ``locate``.
    The route name is stripped of surrounding whitespace before storage.
    Duplicate registration raises ``ValueError``; unknown lookup raises
    ``RouterError``.
    """

    def __init__(self) -> None:
        self._route_table: dict[str, contract.Controller] = {}
        self._documentation_cache: str | None = None

    @property
    def routes(self) -> tuple[str, ...]:
        """All currently registered route names, in insertion order."""

        return tuple(self._route_table.keys())

    def get_route_usage(self, route: str, /) -> str:
        """Return the one-line description of the controller for *route*.

        Collapses the controller's ``__doc__`` into a single space-separated
        string. Returns an empty string if no docstring is present.
        """

        controller_doc = self.locate(route).__doc__
        documentation = " ".join(map(str.strip, controller_doc.split("\n"))) if controller_doc else ""

        return documentation

    def connect(self, route: str, controller: contract.Controller, /) -> None:
        """Register *controller* under *route*.

        Raises:
            ValueError: If *route* is already registered.
        """

        route = route.strip()

        if route in self._route_table:
            raise ValueError("route already exists.")

        self._route_table[route] = controller
        self._documentation_cache = None

    def locate(self, route: str, /) -> contract.Controller:
        """Return the controller bound to *route*.

        Raises:
            RouterError: If *route* is not registered.
        """

        if controller := self._route_table.get(route.strip()):
            return controller

        raise RouterError(route)
