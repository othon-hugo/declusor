from declusor import config, interface


def call_exit(connection: interface.IConnection, console: interface.IConsole, line: str) -> None:
    """Terminate the session and exit the program."""

    raise config.ExitRequest
