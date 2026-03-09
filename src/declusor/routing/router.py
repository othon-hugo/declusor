from declusor import config, interface


class Router(interface.IRouter):
    """Default ``IRouter`` implementation backed by an in-memory dictionary.

    Routes are registered via ``connect`` and dispatched via ``locate``.
    The route name is stripped of surrounding whitespace before storage.
    Duplicate registration raises ``ValueError``; unknown lookup raises
    ``RouterError``.
    """

    def __init__(self) -> None:
        self._route_table: dict[str, interface.Controller] = {}

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

        if controller_doc:
            documentation = " ".join(map(str.strip, controller_doc.split("\n")))
        else:
            documentation = ""

        return documentation

    def connect(self, route: str, controller: interface.Controller, /) -> None:
        """Register *controller* under *route*.

        Raises:
            ValueError: If *route* is already registered.
        """

        route = route.strip()

        if route in self._route_table:
            raise ValueError("route already exists.")

        self._route_table[route] = controller

    def locate(self, route: str, /) -> interface.Controller:
        """Return the controller bound to *route*.

        Raises:
            RouterError: If *route* is not registered.
        """

        if controller := self._route_table.get(route.strip()):
            return controller

        raise config.RouterError(route)

    @property
    def documentation(self) -> str:
        """Formatted help string for all routes, aligned by the longest route name.

        Each line has the form ``route: description``. Returns an empty string
        if no routes are registered.
        """

        if not self._route_table:
            return ""

        key_length = max(map(len, self._route_table.keys())) + 1

        documentation = ""

        for route in self._route_table:
            documentation += f"{route:<{key_length}}: "
            documentation += f"{self.get_route_usage(route)}\n"

        return documentation.rstrip()
