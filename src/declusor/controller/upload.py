from declusor import command, contract


class UploadArguments(contract.ControllerArguments):
    """Arguments for remote file upload."""

    filepath: str
    """Path to local file to encode and store on the remote system."""

    destination: str | None
    """Optional destination path on the remote system."""


def call_upload(
    session: contract.SessionContext,
    req: contract.IControllerRequest[UploadArguments],
) -> contract.ControllerResult:
    """Upload a file from the local system to the remote system."""

    arguments, _ = req.parse_arguments({"filepath": str, "destination": str | None})

    dto = command.UploadFileDTO(
        filepath=arguments["filepath"],
        destination=arguments.get("destination"),
    )
    session.execute(command.UploadFile(dto))

    return contract.ControllerResult.for_continuation()
