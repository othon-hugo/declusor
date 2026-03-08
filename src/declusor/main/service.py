from os import chdir

from declusor import config, connection, controller, core, interface, util


def run_service(router: interface.IRouter, console: interface.IConsole, options: core.DeclusorOptions) -> None:
    """Orchestrate the full server lifecycle for one client session.

    1. Validates required data directories.
    2. Registers all command routes on *router*.
    3. Prints the formatted client bootstrap script.
    4. Listens for a single incoming TCP connection.
    5. Opens a ``ShellSocketConnection``, runs the handshake, then starts
       the interactive prompt loop.

    Args:
        router: Pre-constructed router to register routes on.
        console: Console used for operator I/O throughout the session.
        options: Parsed CLI options (host, port, client profile).

    Raises:
        FileNotFoundError: If a required data directory is missing.
        NotADirectoryError: If a required path exists but is not a directory.
        ConnectionFailure: If the socket cannot be bound or the handshake fails.
    """

    _validate_directories()
    _set_routes(router)

    profile = connection.DEFAULT_SHELL_SOCKET

    console.setup_completer(router.routes)
    console.write_message(profile.render_client_script(options["host"], options["port"]))

    with util.await_connection(options["host"], options["port"]) as socket_connection:
        with connection.ShellSocketConnection(socket_connection, profile) as conn:
            prompt = core.PromptCLI(config.Settings.PROJECT_NAME, router, conn, console)

            conn.initialize()
            prompt.run()


def _validate_directories() -> None:
    """Confirm that all required data directories exist and are directories.

    Also changes the working directory to ``MODULES_DIR`` so that relative
    payload paths work correctly inside the session.

    Raises:
        FileNotFoundError: If any required directory is absent.
        NotADirectoryError: If a required path is not a directory.
    """

    directories = [config.BasePath.CLIENTS_DIR, config.BasePath.MODULES_DIR, config.BasePath.LIBRARY_DIR]

    for directory in directories:
        if directory.exists():
            if not directory.is_dir():
                raise NotADirectoryError(directory)
        else:
            raise FileNotFoundError(directory)

    chdir(config.BasePath.MODULES_DIR)


def _set_routes(router: interface.IRouter) -> None:
    """Register all built-in command routes on *router*."""

    call_help = controller.create_help_controller(lambda: router.documentation, router.get_route_usage)

    router.connect("help", call_help)
    router.connect("load", controller.call_load)
    router.connect("command", controller.call_command)
    router.connect("shell", controller.call_shell)
    router.connect("upload", controller.call_upload)
    router.connect("execute", controller.call_execute)
    router.connect("exit", controller.call_exit)
