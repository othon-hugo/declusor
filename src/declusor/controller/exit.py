from declusor import config, contract


def call_exit(session: contract.IConnection, console: contract.IConsole, line: str) -> None:
    """Terminate the session and exit the program."""

    raise config.ExitRequest
