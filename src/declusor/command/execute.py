from declusor import interface


class ExecuteCommand(interface.ICommand):
    """Send a raw shell command string to the remote client for execution."""

    def __init__(self, command_line: str) -> None:
        """Encode *command_line* as UTF-8 bytes for transmission.

        Args:
            command_line: The shell command to run on the remote system.
        """

        self._command_line = command_line.encode()

    def execute(self, connection: interface.IConnection, console: interface.IConsole, /) -> None:
        """Transmit the command to the remote client.

        Args:
            connection: The active connection to write the command to.
            console: Unused; present to satisfy the ``ICommand`` interface.
        """

        connection.write(self._command_line)
