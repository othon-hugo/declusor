from declusor import command, contract


class UploadArguments(contract.ControllerArguments):
    """Arguments for remote file upload."""

    filepath: str
    """Path to local file to encode and store on the remote system."""


def call_upload(
    session: contract.SessionContext,
    req: contract.IControllerRequest[UploadArguments],
) -> contract.ControllerResult:
    """Upload a file from the local system to the remote system."""

    arguments, _ = req.parse_arguments({"filepath": str})

    dto = command.UploadFileDTO(filepath=arguments["filepath"])
    session.execute(command.UploadFile(dto))

    return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)
