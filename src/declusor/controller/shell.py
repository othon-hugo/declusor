from declusor import command, interface, util


def call_shell(session: interface.IConnection, console: interface.IConsole, line: str) -> None:
    """Initiate an interactive shell session on the remote system."""

    util.parse_command_arguments(line, {})

    command.LaunchShell().execute(session, console)
