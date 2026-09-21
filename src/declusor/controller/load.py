from declusor import command, contract


def call_load(deps: contract.ControllerDependencies, req: contract.ControllerRequest) -> None:
    """Load a selected module from ``data/modules`` on the remote system."""

    arguments, _ = req.parse_arguments({"module": str})
    module_name = arguments["module"]

    command.LoadModule(
        deps.connection,
        deps.console,
        deps.files,
        module_name=module_name,
    ).execute()
