from declusor import command, interface, util


def call_upload(connection: interface.IConnection, console: interface.IConsole, line: str) -> None:
    """Upload a file from the local system to the remote system."""

    arguments, _ = util.parse_command_arguments(line, {"filepath": str})
    filepath = arguments["filepath"]

    command.UploadFile(filepath).execute(connection, console)

    for data in connection.read():
        console.write_binary_data(data)
