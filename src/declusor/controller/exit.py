from declusor import contract


class ExitArguments(contract.ControllerArguments, total=False):
    """Arguments for exit command."""


def call_exit(
    session: contract.SessionContext,
    req: contract.IControllerRequest[ExitArguments],
) -> contract.ControllerResult:
    """Terminate the active interactive session gracefully."""

    return contract.ControllerResult.for_termination()
