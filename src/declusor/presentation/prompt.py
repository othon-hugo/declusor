from declusor import config, contract


class PromptLoop:
    """Interactive command-line loop that reads, routes, and dispatches user input.

    Displays a ``[name] `` prefix on each input line. Handles ``KeyboardInterrupt``
    during input (stops the loop) and during command execution (skips to next
    iteration). Handles ``ControllerAction.TERMINATE`` for clean exit without exceptions.
    ``DeclusorException`` errors are printed to the view without terminating the connection.
    """

    def __init__(
        self,
        name: str,
        /,
        *,
        router: contract.IRouter,
        session: contract.SessionContext,
    ) -> None:
        """Initialize PromptLoop with an active session context.

        Args:
            name: Display name used as prompt prefix (e.g. project name).
            router: Router mapping command routes to controller functions.
            session: Active SessionContext encapsulating connection, view, input, and files.
        """

        self._prompt = f"[{name}] "
        self._router = router
        self._session = session

    @property
    def session(self) -> contract.SessionContext:
        """The active session context."""

        return self._session

    def run(self) -> None:
        """Start the interactive prompt loop.

        Blocks until a controller signals termination (e.g. ``call_exit`` returning
        ``ControllerAction.TERMINATE``) or the user sends ``KeyboardInterrupt`` at the input prompt.
        """

        while True:
            try:
                command_line = self._read_command()
            except KeyboardInterrupt:
                break

            try:
                action = self._route_command(command_line)

                if action == contract.ControllerAction.TERMINATE:
                    break
            except KeyboardInterrupt:
                continue
            except config.DeclusorException as e:
                self._session.view.write_error(e)

    def _read_command(self) -> str:
        """Block until the user enters a non-empty command line.

        Loops (re-prompting) if the stripped line is empty.
        """

        while True:
            if command_line := self._session.input.read_command(self._prompt):
                return command_line

    def _route_command(self, command_line: str) -> contract.ControllerAction:
        """Split *command_line* into a route and an argument, then dispatch.

        The first whitespace-delimited token is the route; the remainder is
        passed as the argument string to the located controller.

        Returns:
            ControllerAction indicating whether to continue or terminate the prompt loop.

        Raises:
            PromptError: If ``command_line`` produces an empty route.
            RouterError: If the route is not registered.
        """

        session = self._session
        result: contract.ControllerResult | contract.ControllerAction | None = None

        match command_line.split(" ", 1):
            case [route, argument]:
                result = self._router.locate(route)(session, contract.ControllerRequest(argument.strip()))
            case [route]:
                result = self._router.locate(route)(session, contract.ControllerRequest())
            case _:
                raise config.PromptError(command_line, "invalid command")

        if isinstance(result, contract.ControllerResult):
            return result.action

        if result == contract.ControllerAction.TERMINATE:
            return contract.ControllerAction.TERMINATE

        return contract.ControllerAction.CONTINUE
