from declusor import config, interface


class PromptCLI(interface.IPrompt):
    """CLI prompt implementation."""

    def __init__(self, name: str, router: interface.IRouter, session: interface.IConnection, console: interface.IConsole) -> None:
        self._prompt = f"[{name}] "

        self._router = router
        self._session = session
        self._console = console

    def run(self) -> None:
        """Run the CLI prompt loop."""

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
        """Read command from user input."""

        while True:
            if command_line := self._console.read_stripped_line(self._prompt):
                return command_line

    def _route_command(self, command_line: str) -> None:
        """Get controler route based on user command."""

        match command_line.split(" ", 1):
            case [route, argument]:
                self._router.locate(route)(self._session, self._console, argument.strip())
            case [route]:
                self._router.locate(route)(self._session, self._console, "")
            case _:
                raise config.PromptError(f"Invalid command: {command_line}")
