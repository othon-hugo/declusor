from declusor import command, contract


def call_shell(deps: contract.ControllerDependencies, req: contract.ControllerRequest) -> None:
    """Initiate an interactive shell session on the remote system."""

    req.parse_arguments({})

    command.LaunchShell(
        deps.connection,
        deps.console,
    ).send_request()
