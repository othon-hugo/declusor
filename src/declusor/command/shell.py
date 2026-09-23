from declusor import contract, util


class LaunchShell(contract.ICommand):
    """Open an interactive bidirectional shell session with the remote client.

    Spawns a background thread to stream responses from the client while the
    main thread forwards the operator's keystrokes. Both threads share a
    ``TaskEvent`` stop-flag for cooperative cancellation.
    A ``KeyboardInterrupt`` (Ctrl-C) tears down both threads and returns
    control to the prompt loop.
    """

    def __init__(
        self,
        connection: contract.IConnection,
        console: contract.IConsole,
    ) -> None:
        super().__init__(connection=connection, console=console)

        self._stop_event = util.TaskEvent()
        self._task_pool = util.TaskPool(self._stop_event)

    def send_request(self) -> None:
        """Start the remote output streaming task in the background."""

        output_streamer = self._create_shell_output_handler(self._connection, self._console)

        self._task_pool.add_task(output_streamer, name="shell_output_streamer")
        self._task_pool.start_all()

    def read_response(self) -> None:
        """Forward operator input in the foreground until interrupted."""

        input_forwarder = self._create_shell_input_handler(self._connection, self._console)

        try:
            input_forwarder(self._stop_event)
            self._task_pool.wait_all()
        except KeyboardInterrupt:
            self._console.write_message("[keyboard interrupt received]")
        finally:
            self._task_pool.stop()

    def _create_shell_input_handler(self, connection: contract.IConnection, console: contract.IConsole, /) -> util.TaskHandler:
        """Return a ``TaskHandler`` that forwards operator input to the remote client.

        Reads lines from *console* and writes non-empty ones to *session*.
        Loops until the shared stop-event is set.
        """

        def _handle_request(stop_event: util.TaskEvent) -> None:
            while not stop_event.is_set():
                command_request = console.read_line()

                if command_request:
                    connection.write(command_request.encode())

        return _handle_request

    def _create_shell_output_handler(self, connection: contract.IConnection, console: contract.IConsole, /) -> util.TaskHandler:
        """Return a ``TaskHandler`` that streams remote output to the console.

        Removes the session timeout for the duration of the shell (blocking
        reads), and restores it when the stop-event fires or an exception
        propagates.
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
