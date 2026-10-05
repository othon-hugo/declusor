import dataclasses
import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING

from declusor import contract, controller, transport

from .launcher import LauncherRenderer

if TYPE_CHECKING:
    from .plugin import PluginManager

TransportListenerFactory = Callable[[str, int], contract.ITransportListener]


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
        listener_factory: TransportListenerFactory | None = None,
        launcher_renderer: LauncherRenderer | None = None,
        transport_registry: transport.TransportLayerRegistry | None = None,
    ) -> None:
        """Create an application with configured dependencies and session runner.

        Args:
            router: Command router resolving interactive prompt input to controller actions.
            view: Operator view interface handling output presentation.
            plugin_manager: Plugin manager containing the available client plugins.
            session_runner: Session runner executing interaction workflows over active sessions.
            input_source: Optional operator input source interface.
            listener_factory: Optional factory producing an ITransportListener for network connections.
            launcher_renderer: Optional renderer responsible for delivering client launcher.
            transport_registry: Optional registry managing composable transport layers.
        """

        self._router = router
        self._view = view
        self._session_runner = session_runner
        self._plugin_manager = plugin_manager
        self._input_source = input_source
        self._listener_factory = listener_factory or transport.TcpListener
        self._launcher_renderer = launcher_renderer or LauncherRenderer(self._view)
        self._transport_registry = transport_registry or transport.default_transport_registry()

        self._connect_routes()

    @property
    def transport_registry(self) -> transport.TransportLayerRegistry:
        """Registry managing available composable transport layers."""

        return self._transport_registry

    @property
    def plugin_manager(self) -> "PluginManager":
        """Active plugin manager managing discovered and registered client plugins."""

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
            params = inspect.signature(setup_completer).parameters
            positional_params = [p for p in params.values() if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)]

            if len(positional_params) >= 2 or "assets_dir" in params:
                setup_completer(self._router.routes, config.filesystem.assets)
            else:
                setup_completer(self._router.routes)

        delivery = plugin_runtime.launcher
        delivery = dataclasses.replace(
            delivery,
            output_mode=config.launcher_output_mode,
            output_path=config.launcher_output_path,
            wrapper_template=config.launcher_wrapper or delivery.wrapper_template,
        )

        self._launcher_renderer.render(delivery)

        with self._listener_factory(config.host, config.port) as listener:
            incoming_transport = listener.accept()

            pipeline = self._transport_registry.build_pipeline(config.transport_layers)
            wrapped_transport = pipeline.wrap(incoming_transport)

            with plugin_runtime.create_connection(wrapped_transport) as connection:
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

        self._router.connect(
            "help",
            contract.RouteRegistration(
                call_help,
                contract.RouteHelp(
                    "Show available commands or detailed help for one command.",
                    "Usage: help [command]. Without an argument, lists commands and their short descriptions.",
                ),
            ),
        )
        self._router.connect(
            "load",
            contract.RouteRegistration(
                controller.call_load,
                contract.RouteHelp(
                    "Load a module on the remote client.", "Usage: load <module>. Loads a module from the configured client module repository."
                ),
            ),
        )
        self._router.connect(
            "command",
            contract.RouteRegistration(
                controller.call_command,
                contract.RouteHelp(
                    "Run a command on the remote client.",
                    "Usage: command <command line>. Executes the command and streams its output to this session.",
                ),
            ),
        )
        self._router.connect(
            "eval",
            contract.RouteRegistration(
                controller.call_eval,
                contract.RouteHelp(
                    "Evaluate code in the client runtime.",
                    "Usage: eval <code>. Executes a code snippet directly in the remote agent's native runtime.",
                ),
            ),
        )
        self._router.connect(
            "shell",
            contract.RouteRegistration(
                controller.call_shell,
                contract.RouteHelp(
                    "Start an interactive remote shell.",
                    "Opens an interactive shell over the active client connection. This command takes no arguments.",
                ),
            ),
        )
        self._router.connect(
            "upload",
            contract.RouteRegistration(
                controller.call_upload,
                contract.RouteHelp(
                    "Upload a local file to the remote client.", "Usage: upload <filepath> [destination]. The destination path is optional."
                ),
            ),
        )
        self._router.connect(
            "execute",
            contract.RouteRegistration(
                controller.call_execute,
                contract.RouteHelp(
                    "Execute a local script on the remote client.",
                    "Usage: execute <filepath>. The script is sent from the local system and executed remotely.",
                ),
            ),
        )
        self._router.connect(
            "exit",
            contract.RouteRegistration(
                controller.call_exit,
                contract.RouteHelp("End the active session.", "Terminates the interactive session gracefully. This command takes no arguments."),
            ),
        )
