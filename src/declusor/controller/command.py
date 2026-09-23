from declusor import command, contract


def call_command(deps: contract.ControllerDependencies, req: contract.ControllerRequest) -> contract.ControllerResult:
    """Execute a single command on the remote system."""

    arguments, _ = req.parse_arguments({"command": str})
    command_line = arguments["command"]

    command.ExecuteCommand(
        connection=deps.connection,
        console=deps.console,
        command_line=command_line,
    ).execute()

    return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)
