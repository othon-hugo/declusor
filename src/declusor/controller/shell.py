from declusor import command, contract


def call_shell(session: contract.SessionContext, req: contract.ControllerRequest) -> contract.ControllerResult:
    """Initiate an interactive shell session on the remote system."""

    req.parse_arguments({})
    session.execute(command.LaunchShell())

    return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)
