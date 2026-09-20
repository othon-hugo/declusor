from declusor import command, contract


def call_upload(session: contract.SessionContext, req: contract.ControllerRequest) -> contract.ControllerResult:
    """Upload a file from the local system to the remote system."""

    arguments, _ = req.parse_arguments({"filepath": str})

    dto = command.UploadFileDTO(filepath=arguments["filepath"])
    session.execute(command.UploadFile(dto))

    return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)
