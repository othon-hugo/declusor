from collections.abc import Callable

from declusor import contract

RouteUsageProvider = Callable[[str], str]


def create_help_controller(routes: tuple[str, ...], get_route_usage: RouteUsageProvider) -> contract.Controller:
    """Create a help controller with documentation providers.

    Args:
        get_documentation: Function that returns full documentation.
        get_route_usage: Function that returns usage for a specific route.

    Returns:
        Help controller function.
    """

    def call_help(session: contract.SessionContext, req: contract.ControllerRequest) -> contract.ControllerResult:
        """Display detailed information about available commands or a specific command."""

        arguments, _ = req.parse_arguments({"command": str | None})

        if help_command := arguments.get("command"):
            session.view.write_message(f"{help_command}: {get_route_usage(help_command)}")
        else:
            route_table: dict[str, str] = {}

            for route in routes:
                route_table[route] = get_route_usage(route).strip()

            key_length = max(map(len, route_table.keys())) + 1

            for route, route_help in route_table.items():
                session.view.write_message(f"{route:<{key_length}}: {route_help}")

        return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)

    return call_help
