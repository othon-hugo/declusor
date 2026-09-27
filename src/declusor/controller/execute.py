from declusor import command, contract


class ExecuteArguments(contract.ControllerArguments):
    """Arguments for remote file execution."""

    filepath: str


def call_execute(
    session: contract.SessionContext,
    req: contract.IControllerRequest[ExecuteArguments],
) -> contract.ControllerResult:
    """Execute a program or script from the local system on the remote system."""

    arguments, _ = req.parse_arguments({"filepath": str})

    dto = command.ExecuteFileDTO(filepath=arguments["filepath"])
    session.execute(command.ExecuteFile(dto))

    return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)
