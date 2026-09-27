from collections.abc import Callable
from typing import TYPE_CHECKING

from declusor import contract, controller, transport

if TYPE_CHECKING:
    from .plugin import PluginManager


class Application:
    """Compose and execute one Declusor server connection.

    Coordinates plugin discovery, route registration, and transport connection
    lifecycle, delegating session interaction to an injected or configured
    ``ISessionRunner``.
    """

    def __init__(
        self,
        router: contract.IRouter,
        view: contract.IView,
        /,
        *,
        plugin_manager: "PluginManager",
        session_runner: contract.ISessionRunner,
        input_source: contract.IInputSource | None = None,
        listener_factory: Callable[[str, int], contract.ITransportListener] | None = None,
    ) -> None:
        """Create an application with configured dependencies and session runner.

        Args:
            router: Command router resolving interactive prompt input to controller actions.
            view: Operator view interface handling output presentation.
            plugin_manager: Plugin manager containing the available client plugins.
            session_runner: Session runner executing interaction workflows over active sessions.
            input_source: Optional operator input source interface.
            listener_factory: Optional factory producing an ITransportListener for network connections.
        """

        self._router = router
        self._view = view
        self._session_runner = session_runner
        self._plugin_manager = plugin_manager
        self._input_source = input_source
        self._listener_factory = listener_factory

        self._connect_routes()

    @property
    def plugin_manager(self) -> "PluginManager":
        return self._plugin_manager

    def register_plugin(self, plugin: type[contract.IPluginExtension[contract.ParsedArguments]], /) -> None:
        """Register a client plugin at runtime.

        Args:
            plugin: Plugin class implementing ``IPlugin``.
        """

        self._plugin_manager.register(plugin)

    def run(self, config: contract.PluginConfig[contract.ParsedArguments], /) -> None:
        """Run the configured server connection.

        Args:
            config: Validated client plugin configuration.

        Raises:
            ConnectionError: If the transport session cannot be established.
        """

        plugin_runtime = self._plugin_manager.get(config.kind).build_runtime(config)

        if self._input_source is not None and (setup_completer := getattr(self._input_source, "setup_completer", None)):
            setup_completer(self._router.routes)

        self._view.write_message(plugin_runtime.launcher)

        listener_factory = self._listener_factory or transport.TcpListener
        with listener_factory(config.host, config.port) as listener:
            incoming_transport = listener.accept()
            with plugin_runtime.create_connection(incoming_transport) as connection:
                connection.handshake()

                session = contract.SessionContext(
                    connection=connection,
                    view=self._view,
                    plugin_processor=plugin_runtime.processor,
                    input_source=self._input_source,
                )

                self._session_runner.run(session, self._router)

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
