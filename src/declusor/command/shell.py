from declusor import interface, util


class LaunchShell(interface.ICommand):
    """Open an interactive bidirectional shell session with the remote client.

    Spawns a background thread to stream responses from the client while the
    main thread forwards the operator's keystrokes. Both threads share a
    ``TaskEvent`` stop-flag for cooperative cancellation.
    A ``KeyboardInterrupt`` (Ctrl-C) tears down both threads and returns
    control to the prompt loop.
    """

    def __init__(self) -> None:
        self._stop_event = util.TaskEvent()
        self._task_pool = util.TaskPool(self._stop_event)

    def execute(self, session: interface.IConnection, console: interface.IConsole, /) -> None:
        """Start the shell session and block until the operator exits.

        Registers the response-reader as a background task, starts it, then
        runs the request-sender in the foreground. Stops all tasks on
        ``KeyboardInterrupt`` or normal completion.

        Args:
            session: The active connection used for bidirectional I/O.
            console: Console for reading operator input and writing output.
        """

        input_handler = self._create_shell_output_handler(session, console)
        output_handler = self._create_shell_input_handler(session, console)

        self._task_pool.add_task(input_handler)
        self._task_pool.start_all()

        try:
            output_handler(self._stop_event)
        except KeyboardInterrupt:
            console.write_message("[keyboard interrupt received]")
        finally:
            self._task_pool.wait_all()
            self._task_pool.stop()

    def _create_shell_input_handler(self, session: interface.IConnection, console: interface.IConsole, /) -> util.TaskHandler:
        """Return a ``TaskHandler`` that forwards operator input to the remote client.

        Reads lines from *console* and writes non-empty ones to *session*.
        Loops until the shared stop-event is set.
        """

        def _handle_request(stop_event: util.TaskEvent) -> None:
            while not stop_event.is_set():
                command_request = console.read_line()

                if command_request:
                    session.write(command_request.encode())

        return _handle_request

    def _create_shell_output_handler(self, session: interface.IConnection, console: interface.IConsole, /) -> util.TaskHandler:
        """Return a ``TaskHandler`` that streams remote output to the console.

        Removes the session timeout for the duration of the shell (blocking
        reads), and restores it when the stop-event fires or an exception
        propagates.
        """

        def _handle_response(stop_event: util.TaskEvent) -> None:
            previous_timeout = session.timeout

            try:
                session.timeout = None

                while not stop_event.is_set():
                    for chunk in session.read():
                        console.write_binary_data(chunk)
            finally:
                session.timeout = previous_timeout

        return _handle_response
