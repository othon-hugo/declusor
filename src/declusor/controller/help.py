from declusor import contract


class HelpArguments(contract.ControllerArguments, total=False):
    """Arguments for help command."""

    command: str | None
    """Optional command route name to query usage help for."""


def create_help_controller(router: contract.IRouter) -> contract.Controller:
    """Create a help controller that queries *router* for routes and help metadata.

    Args:
        router: The application router providing registered routes and help metadata.

    Returns:
        Help controller function.
    """

    def call_help(
        session: contract.SessionContext,
        req: contract.IControllerRequest[HelpArguments],
    ) -> contract.ControllerResult:
        """Display detailed information about available commands or a specific command."""

        arguments, _ = req.parse_arguments({"command": str | None})

        if help_command := arguments.get("command"):
            target_route = help_command.strip()

            if target_route not in router.routes:
                session.view.write_error(f"Unknown command: {target_route!r}. Type 'help' to list available commands.")
                return contract.ControllerResult.for_continuation()

            route_help = router.help(target_route)
            details = "\n\n".join(part for part in (route_help.short, route_help.complement) if part)
            session.view.write_message(details or target_route)
        else:
            routes = router.routes

            if not routes:
                session.view.write_message("No commands available.")
                return contract.ControllerResult.for_continuation()

            key_length = max(map(len, routes)) + 1

            for route in routes:
                short = router.help(route).short
                session.view.write_message(f"{route:<{key_length}}: {short}" if short else route)

        return contract.ControllerResult.for_continuation()

    return call_help
