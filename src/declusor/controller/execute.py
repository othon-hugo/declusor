from declusor import command, contract, util


def call_execute(session: contract.IConnection, console: contract.IConsole, line: str) -> None:
    """Execute a program or script from the local system on the remote system."""

    arguments, _ = util.parse_command_arguments(line, {"filepath": str})
    filepath = arguments["filepath"]

    command.ExecuteFile(filepath).execute(session, console)

    for data in session.read():
        console.write_binary_data(data)
