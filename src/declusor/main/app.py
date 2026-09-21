from collections.abc import Sequence

from declusor import config, controller, core, plugin, util


class Application:
    """Compose and execute one Declusor server connection.

    The application owns concrete dependencies and keeps protocol-specific
    details behind the selected client plugin runtime.
    """

    def __init__(self, registry: core.ClientRegistry, /) -> None:
        """Create an application using a configured client registry.

        Args:
            registry: Registry containing the available client plugins.
        """

        self._registry = registry
        self._router = core.Router()
        self._console = core.Console()

    def parse(self, argv: Sequence[str] | None = None, /) -> core.DeclusorOptions:
        """Parse command-line options using the composed client registry.

        Args:
            argv: Arguments to parse, excluding the executable name. When
                ``None``, arguments are read from the process command line.

        Returns:
            Validated application and client configuration.
        """

        return core.DeclusorParser(
            self._registry,
            name=config.Settings.PROJECT_NAME,
            description=config.Settings.PROJECT_DESCRIPTION,
        ).parse(argv)

    def run(self, options: core.DeclusorOptions, /) -> None:
        """Run the configured server connection.

        Args:
            options: Parsed application and client configuration.

        Raises:
            FileNotFoundError: If a required data directory is missing.
            NotADirectoryError: If a required path is not a directory.
            ConnectionFailure: If the socket session cannot be established.
        """

        self._validate_directories(options["client"].data_paths)
        self._connect_routes()

        client_config = options["client"]
        client_plugin = self._registry.get(client_config.kind)
        client_runtime = client_plugin.build_runtime(client_config)

        self._console.setup_completer(self._router.routes)
        self._console.write_message(client_runtime.client_script)

        with util.await_connection(client_config.host, client_config.port) as socket_connection:
            with client_runtime.create_connection(socket_connection) as connection:
                connection.initialize()

                core.PromptCLI(
                    config.Settings.PROJECT_NAME,
                    router=self._router,
                    connection=connection,
                    console=self._console,
                    files=client_runtime.client_files,
                ).run()

    @staticmethod
    def _validate_directories(data_paths: config.DataPaths, /) -> None:
        """Validate the data directories required by the selected client."""

        directories = (
            data_paths.clients,
            data_paths.modules,
            data_paths.library,
        )

        for directory in directories:
            if not directory.exists():
                raise FileNotFoundError(directory)

            if not directory.is_dir():
                raise NotADirectoryError(directory)

    def _connect_routes(self) -> None:
        """Register built-in command routes on the application router."""

        call_help = controller.create_help_controller(
            lambda: self._router.documentation,
            self._router.get_route_usage,
        )

        self._router.connect("help", call_help)
        self._router.connect("load", controller.call_load)
        self._router.connect("command", controller.call_command)
        self._router.connect("shell", controller.call_shell)
        self._router.connect("upload", controller.call_upload)
        self._router.connect("execute", controller.call_execute)
        self._router.connect("exit", controller.call_exit)


def create_application() -> Application:
    """Create the application with all built-in client plugins registered.

    Returns:
        Fully composed application ready to execute parsed options.
    """

    registry = core.ClientRegistry()
    registry.register(plugin.ShellSocketPlugin)

    return Application(registry)
