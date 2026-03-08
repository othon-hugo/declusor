from declusor import command, interface, util


def call_load(connection: interface.IConnection, console: interface.IConsole, line: str) -> None:
    """Load a payload file from your local system and execute it on the remote system"""

    arguments, _ = util.parse_command_arguments(line, {"filepath": str})
    filepath = arguments["filepath"]

    command.LoadPayload(filepath).execute(connection, console)

    for data in connection.read():
        console.write_binary_data(data)
