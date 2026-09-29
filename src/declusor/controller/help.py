from declusor import contract


class HelpArguments(contract.ControllerArguments, total=False):
    """Arguments for help command."""

    command: str | None
    """[...]"""


def create_help_controller(router: contract.IRouter) -> contract.Controller:
    """Create a help controller that queries *router* for routes and usage descriptions.

    Args:
        router: The application router providing registered routes and route usage.

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
                session.view.write_error(f"Unknown command: '{target_route}'. Type 'help' to list available commands.")
                return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)

            usage = router.help(target_route)
            session.view.write_message(f"{target_route}: {usage}" if usage else target_route)
        else:
            routes = router.routes

            if not routes:
                session.view.write_message("No commands available.")
                return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)

            key_length = max(map(len, routes)) + 1

            for route in routes:
                usage = router.help(route)
                session.view.write_message(f"{route:<{key_length}}: {usage}" if usage else route)

        return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)

    return call_help
