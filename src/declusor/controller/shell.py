from declusor import command, contract, util


def call_shell(session: contract.IConnection, console: contract.IConsole, line: str) -> None:
    """Initiate an interactive shell session on the remote system."""

    util.parse_command_arguments(line, {})

    command.LaunchShell().execute(session, console)
    # Output processing is performed by LaunchShell.
