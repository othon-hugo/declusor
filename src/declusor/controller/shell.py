from declusor import command, contract


class ShellArguments(contract.ControllerArguments, total=False):
    """Arguments for interactive shell session."""


def call_shell(
    session: contract.SessionContext,
    req: contract.IControllerRequest[ShellArguments],
) -> contract.ControllerResult:
    """Launch an interactive pseudo-terminal shell session over the active connection."""

    session.execute(command.LaunchShell())

    return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)
