from declusor import command, contract, util


def call_load(session: contract.IConnection, console: contract.IConsole, line: str) -> None:
    """Load a payload file from your local system and execute it on the remote system"""

    arguments, _ = util.parse_command_arguments(line, {"filepath": str})
    filepath = arguments["filepath"]

    command.LoadPayload(filepath).execute(session, console)

    for data in session.read():
        console.write_binary_data(data)
