from declusor import contract


class ExecuteCommand(contract.ICommand):
    """Send a raw shell command string to the remote client for execution."""

    def __init__(
        self,
        connection: contract.IConnection,
        console: contract.IConsole,
        *,
        command_line: str,
    ) -> None:
        super().__init__(connection=connection, console=console)

        self._command_line = command_line.encode()

    def send_request(self) -> None:
        """[...]"""

        self._connection.write(self._command_line)

    def read_response(self) -> None:
        """[...]"""

        for data in self._connection.read():
            self._console.write_binary_data(data)
