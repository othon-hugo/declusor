from declusor import command, contract


def call_execute(deps: contract.ControllerDependencies, req: contract.ControllerRequest) -> None:
    """Execute a program or script from the local system on the remote system."""

    arguments, _ = req.parse_arguments({"filepath": str})
    filepath = arguments["filepath"]

    command.ExecuteFile(
        deps.connection,
        deps.console,
        filepath=filepath,
    ).execute()
