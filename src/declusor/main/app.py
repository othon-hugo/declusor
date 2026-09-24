from collections.abc import Sequence
from pathlib import Path

from declusor import config, contract, controller, core, presentation, util


class Application:
    """Compose and execute one Declusor server connection.

    The application owns concrete dependencies and keeps protocol-specific
    details behind the selected client plugin runtime.
    """

    def __init__(self, manager: core.ClientPluginManager, /) -> None:
        """Create an application using a configured client plugin manager.

        Args:
            manager: Plugin manager containing the available client plugins.
        """

        self._manager = manager
        self._registry = manager
        self._router = core.Router()
        self._console = presentation.Console()

    @property
    def manager(self) -> core.ClientPluginManager:
        """Client plugin manager containing registered and discovered plugins."""

        return self._manager

    def register_plugin(self, plugin: type[contract.IClientPlugin], /) -> None:
        """Register a client plugin at runtime.

        Args:
            plugin: Plugin class implementing ``IClientPlugin``.
        """

        self._manager.register(plugin)

    def parse(self, argv: Sequence[str] | None = None, /) -> core.DeclusorOptions:
        """Parse command-line options using the composed client registry.

        Args:
            argv: Arguments to parse, excluding the executable name. When
                ``None``, arguments are read from the process command line.

        Returns:
            Validated application and client configuration.
        """

        return core.DeclusorParser(
            self._manager,
            name=config.Settings.PROJECT_NAME,
            description=config.Settings.PROJECT_DESCRIPTION,
        ).parse(argv)

    def run(self, options: core.DeclusorOptions, /) -> None:
        """Run the configured server connection.

        Args:
            options: Parsed application and client configuration.

        Raises:
            ConnectionFailure: If the socket session cannot be established.
        """

        self._connect_routes()

        client_config = options["client"]
        client_plugin = self._manager.get(client_config.kind)
        client_runtime = client_plugin.build_runtime(client_config)

        self._console.setup_completer(self._router.routes)
        self._console.write_message(client_runtime.client_script)

        with util.await_connection(client_config.host, client_config.port) as socket_connection:
            with client_runtime.create_connection(socket_connection) as connection:
                connection.initialize()

                session = contract.SessionContext(
                    connection=connection,
                    console=self._console,
                    files=client_runtime.client_files,
                )

                presentation.PromptCLI(
                    config.Settings.PROJECT_NAME,
                    router=self._router,
                    session=session,
                ).run()

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


def create_application(search_dirs: Sequence[Path] | None = None) -> Application:
    """Create the application with all discovered client plugins registered.

    Runs the multi-tier discovery engine (built-in plugins/, entry points,
    and user drop-in directory) to populate the registry dynamically.

    Args:
        search_dirs: Optional sequence of paths to search for plugins.

    Returns:
        Fully composed application ready to execute parsed options.
    """

    manager = core.ClientPluginManager().discover(search_dirs)

    return Application(manager)
