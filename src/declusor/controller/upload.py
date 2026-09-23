from declusor import command, contract


def call_upload(deps: contract.ControllerDependencies, req: contract.ControllerRequest) -> contract.ControllerResult:
    """Upload a file from the local system to the remote system."""

    arguments, _ = req.parse_arguments({"filepath": str})
    filepath = arguments["filepath"]

    command.UploadFile(
        connection=deps.connection,
        console=deps.console,
        filepath=filepath,
    ).execute()

    return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)
