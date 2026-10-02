from declusor import command, contract


class ShellArguments(contract.ControllerArguments, total=False):
    """Arguments for interactive shell session."""


def call_shell(
    session: contract.SessionContext,
    req: contract.IControllerRequest[ShellArguments],
) -> contract.ControllerResult:
    """Launch an interactive pseudo-terminal shell session over the active connection."""

    dto = command.LaunchShellDTO()
    session.execute(command.LaunchShell(dto))

    return contract.ControllerResult.for_continuation()
