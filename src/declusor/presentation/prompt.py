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
        connection: contract.IConnection,
        console: contract.IConsole,
        files: contract.IClientFileStore,
    ) -> None:
        self._prompt = f"[{name}] "

        self._router = router
        self._connection = connection
        self._console = console
        self._files = files

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
            except config.ExitRequest:
                break
            except KeyboardInterrupt:
                continue
            except config.DeclusorException as e:
                self._console.write_error_message(e)

    def _read_command(self) -> str:
        """Block until the user enters a non-empty command line.

        Loops (re-prompting) if the stripped line is empty.
        """

        while True:
            if command_line := self._console.read_stripped_line(self._prompt):
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

        deps = contract.ControllerDependencies(self._connection, self._console, self._files)
        result: contract.ControllerResult | contract.ControllerAction | None = None

        match command_line.split(" ", 1):
            case [route, argument]:
                result = self._router.locate(route)(deps, contract.ControllerRequest(argument.strip()))
            case [route]:
                result = self._router.locate(route)(deps, contract.ControllerRequest())
            case _:
                raise config.PromptError(f"Invalid command: {command_line}")

        if isinstance(result, contract.ControllerResult):
            return result.action

        if result == contract.ControllerAction.TERMINATE:
            return contract.ControllerAction.TERMINATE

        return contract.ControllerAction.CONTINUE
