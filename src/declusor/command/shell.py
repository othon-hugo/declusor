from dataclasses import dataclass

from declusor import contract, util


@dataclass(frozen=True)
class LaunchShellDTO:
    """Data transfer object configuring an interactive shell session.

    Attributes:
        banner: Optional informational banner message displayed upon entering shell mode.
    """

    banner: str | None = None


class LaunchShell(contract.ICommand):
    """Open an interactive bidirectional shell session with the remote client.

    Spawns a background thread to stream output from the client while the main
    thread reads and forwards the operator's keystrokes. Both threads share a
    cooperative ``TaskEvent`` stop-flag. A ``KeyboardInterrupt`` (Ctrl-C) cleanly
    shuts down the streaming task and returns control to the REPL prompt loop.

    Attributes:
        dto: Configuration options for the shell session.
    """

    def __init__(self, dto: LaunchShellDTO | None = None) -> None:
        """Initialize the interactive shell command.

        Args:
            dto: Optional configuration DTO for the shell session.
        """

        super().__init__()

        self._dto = dto or LaunchShellDTO()
        self._stop_event = util.TaskEvent()
        self._task_pool = util.TaskPool(self._stop_event)

    @property
    def dto(self) -> LaunchShellDTO:
        """The command parameters."""

        return self._dto

    def send_request(self, session: contract.SessionContext) -> None:
        """Start the background task that streams remote client output to the console.

        Args:
            session: Active session context providing connection and console.
        """

        output_streamer = self._create_shell_output_handler(
            session.connection,
            session.console,
        )

        self._task_pool.add_task(output_streamer, name="shell_output_streamer")
        self._task_pool.start_all()

    def read_response(self, session: contract.SessionContext) -> None:
        """Forward operator input from the console to the remote client until interrupted.

        Args:
            session: Active session context providing connection and console.
        """

        input_forwarder = self._create_shell_input_handler(
            session.connection,
            session.console,
        )

        try:
            if self._dto.banner:
                session.console.write_message(self._dto.banner)

            input_forwarder(self._stop_event)
            self._task_pool.wait_all()
        except KeyboardInterrupt:
            session.console.write_message("[keyboard interrupt received]")
        finally:
            self._task_pool.stop()

    def _create_shell_input_handler(
        self,
        connection: contract.IConnection,
        console: contract.IConsole,
        /,
    ) -> util.TaskHandler:
        """Return a TaskHandler that reads lines from console and sends them over the connection.

        Args:
            connection: Active client connection.
            console: Operator console interface.

        Returns:
            A callable task handler for execution in the thread pool or loop.
        """

        def _handle_request(stop_event: util.TaskEvent) -> None:
            while not stop_event.is_set():
                command_request = console.read_line()

                if command_request:
                    connection.write(command_request.encode())

        return _handle_request

    def _create_shell_output_handler(
        self,
        connection: contract.IConnection,
        console: contract.IConsole,
        /,
    ) -> util.TaskHandler:
        """Return a TaskHandler that streams client output to the console.

        Temporarily clears the connection timeout for blocking reads and restores
        it on completion.

        Args:
            connection: Active client connection.
            console: Operator console interface.

        Returns:
            A callable task handler for execution in the background task pool.
        """

        def _handle_response(stop_event: util.TaskEvent) -> None:
            previous_timeout = connection.timeout

            try:
                connection.timeout = None

                while not stop_event.is_set():
                    for chunk in connection.read():
                        console.write_binary_data(chunk)
            finally:
                connection.timeout = previous_timeout

        return _handle_response
