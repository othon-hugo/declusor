from types import MappingProxyType

from declusor import contract, controller

OFFICIAL_ROUTES: contract.RouteTable = MappingProxyType(
    {
        "load": contract.RouteRegistration(
            controller.call_load,
            contract.RouteHelp(
                "Load a module on the remote client.",
                "Usage: load <module>. Loads a module from the configured client module repository.",
            ),
        ),
        "command": contract.RouteRegistration(
            controller.call_command,
            contract.RouteHelp(
                "Run a command on the remote client.",
                "Usage: command <command line>. Executes the command and streams its output to this session.",
            ),
        ),
        "eval": contract.RouteRegistration(
            controller.call_eval,
            contract.RouteHelp(
                "Evaluate code in the client runtime.",
                "Usage: eval <code>. Executes a code snippet directly in the remote agent's native runtime.",
            ),
        ),
        "shell": contract.RouteRegistration(
            controller.call_shell,
            contract.RouteHelp(
                "Start an interactive remote shell.",
                "Opens an interactive shell over the active client connection. This command takes no arguments.",
            ),
        ),
        "upload": contract.RouteRegistration(
            controller.call_upload,
            contract.RouteHelp(
                "Upload a local file to the remote client.",
                "Usage: upload <filepath> [destination]. The destination path is optional.",
            ),
        ),
        "execute": contract.RouteRegistration(
            controller.call_execute,
            contract.RouteHelp(
                "Execute a local script on the remote client.",
                "Usage: execute <filepath>. The script is sent from the local system and executed remotely.",
            ),
        ),
    }
)
"""Official plugin-specific routes that plugins may reuse or override."""


EXIT_ROUTE = contract.RouteRegistration(
    controller.call_exit,
    contract.RouteHelp(
        "End the active session.",
        "Terminates the interactive session gracefully. This command takes no arguments.",
    ),
)


def create_help_route(router: contract.IRouter, /) -> contract.RouteRegistration:
    """Create the protected help route bound to *router*."""

    return contract.RouteRegistration(
        controller.create_help_controller(router),
        contract.RouteHelp(
            "Show available commands or detailed help for one command.",
            "Usage: help [command]. Without an argument, lists commands and their short descriptions.",
        ),
    )
