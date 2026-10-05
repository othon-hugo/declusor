from declusor import command, contract


class EvalArguments(contract.ControllerArguments):
    """Arguments for evaluating native client runtime code."""

    code: str
    """Client runtime code snippet to evaluate remotely."""


def call_eval(
    session: contract.SessionContext,
    req: contract.IControllerRequest[EvalArguments],
) -> contract.ControllerResult:
    """Execute native client runtime code directly on the remote agent."""

    arguments, _ = req.parse_arguments({"code": str})

    dto = command.ExecuteCodeDTO(code=arguments["code"])
    session.execute(command.ExecuteCode(dto))

    return contract.ControllerResult.for_continuation()
