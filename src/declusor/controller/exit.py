from declusor import config, contract


def call_exit(deps: contract.ControllerDependencies, req: contract.ControllerRequest) -> None:
    """Terminate the session and exit the program."""

    raise config.ExitRequest
