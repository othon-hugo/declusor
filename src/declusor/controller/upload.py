from declusor import command, contract


def call_upload(deps: contract.ControllerDependencies, req: contract.ControllerRequest) -> None:
    """Upload a file from the local system to the remote system."""

    arguments, _ = req.parse_arguments({"filepath": str})
    filepath = arguments["filepath"]

    command.UploadFile(
        deps.connection,
        deps.console,
        filepath=filepath,
    ).execute()
