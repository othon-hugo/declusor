from declusor import command, interface, util


def call_shell(connection: interface.IConnection, console: interface.IConsole, line: str) -> None:
    """Initiate an interactive shell session on the remote system."""

    util.parse_command_arguments(line, {})

    command.LaunchShell().execute(connection, console)
    # Output processing is performed by LaunchShell.
