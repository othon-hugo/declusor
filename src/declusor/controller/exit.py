from declusor import config, interface


def call_exit(session: interface.IConnection, console: interface.IConsole, line: str) -> None:
    """Terminate the session and exit the program."""

    raise config.ExitRequest
