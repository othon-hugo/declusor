from typing import Protocol, runtime_checkable

from declusor import contract, controller, core, util


@runtime_checkable
class ApplicationProtocol(Protocol):
    """Protocol defining the interface required by the CLI to run an application."""

    @property
    def manager(self) -> core.PluginManager:
        """Client plugin manager containing registered plugins."""
        ...

    def run(self, config: contract.PluginConfig, /) -> None:
        """Execute the application lifecycle for a given plugin configuration."""
        ...


class Application(ApplicationProtocol):
    """Compose and execute one Declusor server connection.

    Coordinates plugin discovery, route registration, and transport connection
    lifecycle, delegating session interaction to an injected or configured
    ``ISessionRunner``.
    """

    def __init__(
        self,
        manager: core.PluginManager,
        router: contract.IRouter,
        view: contract.IView,
        runner: contract.ISessionRunner,
        input_source: contract.IInputSource | None = None,
        /,
    ) -> None:
        """Create an application with configured dependencies and session runner.

        Args:
            manager: Plugin manager containing the available client plugins.
            router: Command router resolving interactive prompt input to controller actions.
            view: Operator view interface handling output presentation.
            runner: Session runner executing interaction workflows over active sessions.
            input_source: Optional operator input source interface.
        """

        self._manager = manager
        self._router = router
        self._view = view
        self._runner = runner
        self._input_source = input_source

        self._connect_routes()

    @property
    def manager(self) -> core.PluginManager:
        """Client plugin manager containing registered and discovered plugins."""

        return self._manager

    @property
    def runner(self) -> contract.ISessionRunner:
        """The active session runner."""

        return self._runner

    @runner.setter
    def runner(self, runner: contract.ISessionRunner) -> None:
        """Set or replace the session runner at runtime."""

        self._runner = runner

    def register_plugin(self, plugin: type[contract.IPlugin], /) -> None:
        """Register a client plugin at runtime.

        Args:
            plugin: Plugin class implementing ``IPlugin``.
        """

        self._manager.register(plugin)

    def run(
        self,
        config: contract.PluginConfig,
        /,
        *,
        runner: contract.ISessionRunner | None = None,
    ) -> None:
        """Run the configured server connection.

        Args:
            config: Validated client plugin configuration.
            runner: Optional session runner overriding the default runner for this execution.

        Raises:
            ConnectionFailure: If the socket session cannot be established.
        """

        plugin_runtime = self._manager.get(config.kind).build_runtime(config)

        if self._input_source is not None and (setup_completer := getattr(self._input_source, "setup_completer", None)):
            setup_completer(self._router.routes)

        self._view.write_message(plugin_runtime.client_script)

        with util.await_connection(config.host, config.port) as socket_connection:
            with plugin_runtime.create_connection(socket_connection) as connection:
                connection.initialize()

                session = contract.SessionContext(
                    connection=connection,
                    view=self._view,
                    input=self._input_source,
                    files=plugin_runtime.client_files,
                )

                active_runner = runner if runner is not None else self._runner
                active_runner.run(session, self._router)

    def _connect_routes(self) -> None:
        """Register built-in command routes on the application router."""

        call_help = controller.create_help_controller(self._router)

        self._router.connect("help", call_help)
        self._router.connect("load", controller.call_load)
        self._router.connect("command", controller.call_command)
        self._router.connect("shell", controller.call_shell)
        self._router.connect("upload", controller.call_upload)
        self._router.connect("execute", controller.call_execute)
        self._router.connect("exit", controller.call_exit)
