from declusor import command, contract


def call_command(deps: contract.ControllerDependencies, req: contract.ControllerRequest) -> None:
    """Execute a single command on the remote system."""

    arguments, _ = req.parse_arguments({"command": str})
    command_line = arguments["command"]

    command.ExecuteCommand(
        deps.connection,
        deps.console,
        command_line=command_line,
    ).execute()
