from os import chdir

from declusor import config, connection, controller, core, interface, util


def run_service(router: interface.IRouter, console: interface.IConsole, options: core.DeclusorOptions) -> None:
    """Run the main service loop."""

    _validate_directories()
    _set_routes(router)

    profile = connection.DEFAULT_SHELL_SOCKET

    console.setup_completer(router.routes)
    console.write_message(profile.format_client_script(options["host"], options["port"]))

    with util.await_connection(options["host"], options["port"]) as socket_connection:
        profile_connection = connection.ShellSocketConnection(socket_connection, profile)

        try:
            prompt = core.PromptCLI(config.Settings.PROJECT_NAME, router, profile_connection, console)

            profile_connection.initialize()
            prompt.run()
        finally:
            profile_connection.close()


def _validate_directories() -> None:
    """Validate that all required data directories exist."""

    directories = [config.BasePath.CLIENTS_DIR, config.BasePath.MODULES_DIR, config.BasePath.LIBRARY_DIR]

    for directory in directories:
        if directory.exists():
            if not directory.is_dir():
                raise NotADirectoryError(directory)
        else:
            raise FileNotFoundError(directory)

    chdir(config.BasePath.MODULES_DIR)


def _set_routes(router: interface.IRouter) -> None:
    """Set up the routes for the router."""

    call_help = controller.create_help_controller(lambda: router.documentation, router.get_route_usage)

    router.connect("help", call_help)
    router.connect("load", controller.call_load)
    router.connect("command", controller.call_command)
    router.connect("shell", controller.call_shell)
    router.connect("upload", controller.call_upload)
    router.connect("execute", controller.call_execute)
    router.connect("exit", controller.call_exit)
