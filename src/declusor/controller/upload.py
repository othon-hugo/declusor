from declusor import command, contract, util


def call_upload(session: contract.IConnection, console: contract.IConsole, line: str) -> None:
    """Upload a file from the local system to the remote system."""

    arguments, _ = util.parse_command_arguments(line, {"filepath": str})
    filepath = arguments["filepath"]

    command.UploadFile(filepath).execute(session, console)

    for data in session.read():
        console.write_binary_data(data)
