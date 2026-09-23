from collections.abc import Callable

from declusor import contract

DocumentationProvider = Callable[[], str]
RouteUsageProvider = Callable[[str], str]


def create_help_controller(get_documentation: DocumentationProvider, get_route_usage: RouteUsageProvider) -> contract.Controller:
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
            session.console.write_message(f"{help_command}: {get_route_usage(help_command)}")
        else:
            session.console.write_message(get_documentation())

        return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)

    return call_help
