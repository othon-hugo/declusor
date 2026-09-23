from declusor import contract


def call_exit(deps: contract.ControllerDependencies, req: contract.ControllerRequest) -> contract.ControllerResult:
    """Terminate the session and exit the program."""

    return contract.ControllerResult(action=contract.ControllerAction.TERMINATE)
