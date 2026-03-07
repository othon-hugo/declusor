from declusor import command, interface, util


def call_load(session: interface.IConnection, console: interface.IConsole, line: str) -> None:
    """Load a payload file from your local system and execute it on the remote system"""

    arguments, _ = util.parse_command_arguments(line, {"filepath": str})
    filepath = util.ensure_file_exists(arguments["filepath"])

    util.handle_command(command.LoadPayload(filepath), session, console)
