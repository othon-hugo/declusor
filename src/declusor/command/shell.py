from declusor import interface, util


class LaunchShell(interface.ICommand):
    """Command to launch an interactive shell session."""

    def __init__(self) -> None:
        self._stop_event = util.TaskEvent()
        self._task_pool = util.TaskPool(self._stop_event)

    def execute(self, session: interface.IConnection, console: interface.IConsole, /) -> None:
        """Execute the interactive shell session.

        Args:
            session: The active session.
            console: The console interface for user interaction.
        """

        response_handler = self._create_response_handler(session, console)
        request_handler = self._create_request_handler(session, console)

        self._task_pool.add_task(response_handler)
        self._task_pool.start_all()

        try:
            request_handler(self._stop_event)

            self._task_pool.wait_all()
        except KeyboardInterrupt:
            console.write_message("[keyboard interrupt received]")
        finally:
            self._task_pool.stop()

    def _create_request_handler(self, session: interface.IConnection, console: interface.IConsole, /) -> util.TaskHandler:
        """Handle reading commands from user input and sending them to the session."""

        def _handle_request(stop_event: util.TaskEvent) -> None:
            while not stop_event.is_set():
                command_request = console.read_line()

                if command_request:
                    session.write(command_request.encode())

        return _handle_request

    def _create_response_handler(self, session: interface.IConnection, console: interface.IConsole, /) -> util.TaskHandler:
        """Handle reading responses from the session and displaying them to the user."""

        def _handle_response(stop_event: util.TaskEvent) -> None:
            previous_timeout = session.timeout

            try:
                session.timeout = None

                while not stop_event.is_set():
                    for chunk in session.read():
                        if chunk:
                            console.write_binary_data(chunk)
            finally:
                session.timeout = previous_timeout

        return _handle_response
