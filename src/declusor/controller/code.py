from declusor import command, contract


class CodeArguments(contract.ControllerArguments):
    """Arguments for native client runtime code execution."""

    code: str
    """Client runtime code snippet to evaluate remotely."""


def call_code(
    session: contract.SessionContext,
    req: contract.IControllerRequest[CodeArguments],
) -> contract.ControllerResult:
    """Execute native client runtime code directly on the remote agent."""

    arguments, _ = req.parse_arguments({"code": str})

    dto = command.ExecuteCodeDTO(code=arguments["code"])
    session.execute(command.ExecuteCode(dto))

    return contract.ControllerResult.for_continuation()
