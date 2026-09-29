from declusor import command, contract


class CommandArguments(contract.ControllerArguments):
    """Arguments for command execution."""

    command: str
    """[...]"""


def call_command(
    session: contract.SessionContext,
    req: contract.IControllerRequest[CommandArguments],
) -> contract.ControllerResult:
    """Execute a single command on the remote system."""

    arguments, _ = req.parse_arguments({"command": str})

    dto = command.ExecuteCommandDTO(command_line=arguments["command"])
    session.execute(command.ExecuteCommand(dto))

    return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)
