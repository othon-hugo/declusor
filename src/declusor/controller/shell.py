from declusor import command, contract


def call_shell(deps: contract.ControllerDependencies, req: contract.ControllerRequest) -> contract.ControllerResult:
    """Initiate an interactive shell session on the remote system."""

    req.parse_arguments({})

    command.LaunchShell(
        connection=deps.connection,
        console=deps.console,
    ).execute()

    return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)
