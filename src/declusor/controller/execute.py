from declusor import command, contract


def call_execute(session: contract.SessionContext, req: contract.ControllerRequest) -> contract.ControllerResult:
    """Execute a program or script from the local system on the remote system."""
    arguments, _ = req.parse_arguments({"filepath": str})

    dto = command.ExecuteFileDTO(filepath=arguments["filepath"])
    session.execute(command.ExecuteFile(dto))

    return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)
