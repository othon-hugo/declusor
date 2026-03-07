from declusor import command, interface, util


def call_command(session: interface.IConnection, console: interface.IConsole, line: str) -> None:
    """Execute a single command on the remote system."""

    arguments, _ = util.parse_command_arguments(line, {"command": str})
    command_line = arguments["command"]

    command.ExecuteCommand(command_line).execute(session, console)

    for data in session.read():
        console.write_binary_data(data)
