from declusor import contract


def call_exit(session: contract.SessionContext, req: contract.ControllerRequest) -> contract.ControllerResult:
    """Terminate the session and exit the program."""

    return contract.ControllerResult(action=contract.ControllerAction.TERMINATE)
