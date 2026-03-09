from declusor import config, interface


class PromptCLI(interface.IPrompt):
    """Readline-backed interactive prompt that routes commands to registered controllers.

    Displays a ``[name] `` prefix on each input line. Handles ``KeyboardInterrupt``
    during input (stops the loop) and during command execution (skips to next
    iteration). ``DeclusorException`` errors are printed to the console without
    terminating the session.
    """

    def __init__(self, name: str, router: interface.IRouter, connection: interface.IConnection, console: interface.IConsole) -> None:
        self._prompt = f"[{name}] "

        self._router = router
        self._connection = connection
        self._console = console

    def run(self) -> None:
        """Start the interactive prompt loop.

        Blocks until ``ExitRequest`` is raised by a controller (e.g. ``call_exit``)
        or the user sends ``KeyboardInterrupt`` at the input prompt.
        """

        while True:
            try:
                command_line = self._read_command()
            except KeyboardInterrupt:
                break

            try:
                self._route_command(command_line)
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

    def _route_command(self, command_line: str) -> None:
        """Split *command_line* into a route and an argument, then dispatch.

        The first whitespace-delimited token is the route; the remainder is
        passed as the argument string to the located controller.

        Raises:
            PromptError: If ``command_line`` produces an empty route.
            RouterError: If the route is not registered.
        """

        match command_line.split(" ", 1):
            case [route, argument]:
                self._router.locate(route)(self._connection, self._console, argument.strip())
            case [route]:
                self._router.locate(route)(self._connection, self._console, "")
            case _:
                raise config.PromptError(f"Invalid command: {command_line}")
