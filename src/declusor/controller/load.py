from declusor import command, contract


def call_load(session: contract.SessionContext, req: contract.ControllerRequest) -> contract.ControllerResult:
    """Load a selected module from ``data/modules`` on the remote system."""

    arguments, _ = req.parse_arguments({"module": str})

    dto = command.LoadModuleDTO(module_name=arguments["module"])
    session.execute(command.LoadModule(dto))

    return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)
