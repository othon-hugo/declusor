from declusor import config, contract


class PromptLoop(contract.ISessionRunner):
    """Interactive command-line loop that reads, routes, and dispatches user input.

    Displays a ``[name] `` prefix on each input line. Handles ``KeyboardInterrupt``
    during input (stops the loop) and during command execution (skips to next
    iteration). Handles ``ControllerAction.TERMINATE`` for clean exit without exceptions.
    ``DeclusorException`` errors are printed to the view without terminating the connection.
    """

    def __init__(
        self,
        name: str = config.Settings.PROJECT_NAME,
        /,
        *,
        router: contract.IRouter | None = None,
        session: contract.SessionContext | None = None,
    ) -> None:
        """Initialize PromptLoop with an optional prompt prefix name, router, and session.

        Args:
            name: Display name used as prompt prefix (e.g. project name).
            router: Optional router mapping command routes to controller functions.
            session: Optional active SessionContext encapsulating connection, view, input, and files.
        """

        self._prompt = f"[{name}] "
        self._router = router
        self._session = session

    @property
    def session(self) -> contract.SessionContext | None:
        """The active session context, if configured at initialization."""

        return self._session

    def run(
        self,
        session: contract.SessionContext | None = None,
        router: contract.IRouter | None = None,
        /,
    ) -> None:
        """Start the interactive prompt loop.

        Blocks until a controller signals termination (e.g. ``call_exit`` returning
        ``ControllerAction.TERMINATE``) or the user sends ``KeyboardInterrupt`` at the input prompt.

        Args:
            session: Active session context to drive. Defaults to session provided in constructor.
            router: Router resolving routes to controllers. Defaults to router provided in constructor.

        Raises:
            PromptError: If session or router is missing, or if session has no input source.
        """

        active_session = session or self._session
        active_router = router or self._router

        if active_session is None or active_router is None:
            raise config.PromptError(self._prompt, "PromptLoop requires an active session and router.")

        if active_session.input is None:
            raise config.PromptError(self._prompt, "PromptLoop requires an active session with an input source.")

        while True:
            try:
                command_line = self._read_command(active_session)
            except KeyboardInterrupt:
                break

            try:
                action = self._route_command(command_line, active_session, active_router)

                if action == contract.ControllerAction.TERMINATE:
                    break
            except KeyboardInterrupt:
                continue
            except config.DeclusorException as e:
                active_session.view.write_error(e)

    def _read_command(self, session: contract.SessionContext) -> str:
        """Block until the user enters a non-empty command line.

        Loops (re-prompting) if the stripped line is empty.
        """

        if session.input is None:
            raise config.PromptError(self._prompt, "Input source is not available.")

        while True:
            if command_line := session.input.read_command(self._prompt):
                return command_line

    def _route_command(
        self,
        command_line: str,
        session: contract.SessionContext,
        router: contract.IRouter,
    ) -> contract.ControllerAction:
        """Split *command_line* into a route and an argument, then dispatch.

        The first whitespace-delimited token is the route; the remainder is
        passed as the argument string to the located controller.

        Returns:
            ControllerAction indicating whether to continue or terminate the prompt loop.

        Raises:
            PromptError: If ``command_line`` produces an empty route.
            RouterError: If the route is not registered.
        """

        result: contract.ControllerResult | contract.ControllerAction | None = None

        match command_line.split(" ", 1):
            case [route, argument]:
                result = router.locate(route)(session, contract.ControllerRequest(argument.strip()))
            case [route]:
                result = router.locate(route)(session, contract.ControllerRequest())
            case _:
                raise config.PromptError(command_line, "invalid command")

        if isinstance(result, contract.ControllerResult):
            return result.action

        if result == contract.ControllerAction.TERMINATE:
            return contract.ControllerAction.TERMINATE

        return contract.ControllerAction.CONTINUE
