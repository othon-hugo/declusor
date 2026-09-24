from declusor import config, contract


class PromptCLI(contract.IPrompt):
    """Readline-backed interactive prompt that routes commands to registered controllers.

    Displays a ``[name] `` prefix on each input line. Handles ``KeyboardInterrupt``
    during input (stops the loop) and during command execution (skips to next
    iteration). Handles ``ControllerAction.TERMINATE`` for clean exit without exceptions.
    ``DeclusorException`` errors are printed to the console without terminating the connection.
    """

    def __init__(
        self,
        name: str,
        /,
        *,
        router: contract.IRouter,
        session: contract.SessionContext | None = None,
        connection: contract.IConnection | None = None,
        console: contract.IConsole | None = None,
        files: contract.IPluginFileStore | None = None,
    ) -> None:
        """Initialize PromptCLI with an active session or individual session components.

        Args:
            name: Display name used as prompt prefix (e.g. project name).
            router: Router mapping command routes to controller functions.
            session: Active SessionContext encapsulating connection, console, and files.
            connection: Fallback connection if session is not directly passed.
            console: Fallback console if session is not directly passed.
            files: Fallback client file store if session is not directly passed.
        """

        self._prompt = f"[{name}] "
        self._router = router

        if session is not None:
            self._session = session
        elif connection is not None and console is not None and files is not None:
            self._session = contract.SessionContext(
                connection=connection,
                console=console,
                files=files,
            )
        else:
            raise config.InvalidOperation("Either session or (connection, console, files) must be provided.")

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
                self._session.console.write_error_message(e)

    def _read_command(self) -> str:
        """Block until the user enters a non-empty command line.

        Loops (re-prompting) if the stripped line is empty.
        """

        while True:
            if command_line := self._session.console.read_stripped_line(self._prompt):
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
