from declusor import command, contract


def call_load(deps: contract.ControllerDependencies, req: contract.ControllerRequest) -> contract.ControllerResult:
    """Load a selected module from ``data/modules`` on the remote system."""

    arguments, _ = req.parse_arguments({"module": str})
    module_name = arguments["module"]

    command.LoadModule(
        connection=deps.connection,
        console=deps.console,
        files=deps.files,
        module_name=module_name,
    ).execute()

    return contract.ControllerResult(action=contract.ControllerAction.CONTINUE)
