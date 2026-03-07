from declusor import command, interface, util


def call_execute(session: interface.IConnection, console: interface.IConsole, line: str) -> None:
    """Execute a program or script from the local system on the remote system."""

    arguments, _ = util.parse_command_arguments(line, {"filepath": str})
    filepath = util.ensure_file_exists(arguments["filepath"])

    util.handle_command(command.ExecuteFile(filepath), session, console)
