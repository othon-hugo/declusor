from declusor import command, interface, util


def call_upload(session: interface.IConnection, console: interface.IConsole, line: str) -> None:
    """Upload a file from the local system to the remote system."""

    arguments, _ = util.parse_command_arguments(line, {"filepath": str})
    filepath = util.ensure_file_exists(arguments["filepath"])

    util.handle_command(command.UploadFile(filepath), session, console)
