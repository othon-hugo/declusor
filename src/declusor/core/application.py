import dataclasses
import inspect
from collections.abc import Callable
from typing import TYPE_CHECKING

from declusor import config, contract, controller, transport
from declusor.config import InvalidOperation

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
        launcher_renderer: LauncherRenderer | None = None,
        transport_registry: transport.TransportLayerRegistry | None = None,
        listener_factory: TransportListenerFactory | None = None,
    ) -> None:
        """Create an application with configured dependencies and session runner.

        Args:
            router: Command router resolving interactive prompt input to controller actions.
            view: Operator view interface handling output presentation.
            plugin_manager: Plugin manager containing the available client plugins.
            session_runner: Session runner executing interaction workflows over active sessions.
            input_source: Optional operator input source interface.
            launcher_renderer: Optional renderer responsible for delivering client launcher.
            transport_registry: Optional registry managing composable transport layers.
            listener_factory: Optional factory producing an ITransportListener for network connections.
        """

        self._router = router
        self._view = view
        self._session_runner = session_runner
        self._plugin_manager = plugin_manager
        self._input_source = input_source
        self._launcher_renderer = launcher_renderer or LauncherRenderer(self._view)
        self._transport_registry = transport_registry or transport.default_transport_registry()
        self._listener_factory = listener_factory or transport.TcpListener
        self._route_plugin_name: str | None = None

    @property
    def router(self) -> contract.IRouter:
        """Active command router resolving interactive commands to controller actions."""

        return self._router

    @property
    def view(self) -> contract.IView:
        """Operator presentation view interface."""

        return self._view

    @property
    def plugin_manager(self) -> "PluginManager":
        """Active plugin manager managing discovered and registered client plugins."""

        return self._plugin_manager

    @property
    def session_runner(self) -> contract.ISessionRunner:
        """Active session runner executing prompt workflows."""

        return self._session_runner

    @property
    def input_source(self) -> contract.IInputSource | None:
        """Operator input source interface reading commands, or None if omitted."""

        return self._input_source

    @property
    def transport_registry(self) -> transport.TransportLayerRegistry:
        """Registry managing available composable transport layers."""

        return self._transport_registry

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

        plugin_class = self._plugin_manager.get(config.kind)

        if self._route_plugin_name is None:
            self._connect_routes(plugin_class.supported_controllers)
            self._route_plugin_name = plugin_class.name
        elif self._route_plugin_name != plugin_class.name:
            raise InvalidOperation(
                f"Application routes are already configured for plugin '{self._route_plugin_name}'. "
                f"Create a new Application to use '{plugin_class.name}'."
            )

        plugin_runtime = plugin_class.build_runtime(config)

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

    def _connect_routes(self, supported_controllers: frozenset[config.ControllerType], /) -> None:
        """Register universal and plugin-supported routes on the application router."""

        registrations = {
            config.ControllerType.HELP: contract.RouteRegistration(
                controller.create_help_controller(self._router),
                contract.RouteHelp(
                    "Show available commands or detailed help for one command.",
                    "Usage: help [command]. Without an argument, lists commands and their short descriptions.",
                ),
            ),
            config.ControllerType.LOAD: contract.RouteRegistration(
                controller.call_load,
                contract.RouteHelp(
                    "Load a module on the remote client.", "Usage: load <module>. Loads a module from the configured client module repository."
                ),
            ),
            config.ControllerType.COMMAND: contract.RouteRegistration(
                controller.call_command,
                contract.RouteHelp(
                    "Run a command on the remote client.",
                    "Usage: command <command line>. Executes the command and streams its output to this session.",
                ),
            ),
            config.ControllerType.EVAL: contract.RouteRegistration(
                controller.call_eval,
                contract.RouteHelp(
                    "Evaluate code in the client runtime.",
                    "Usage: eval <code>. Executes a code snippet directly in the remote agent's native runtime.",
                ),
            ),
            config.ControllerType.SHELL: contract.RouteRegistration(
                controller.call_shell,
                contract.RouteHelp(
                    "Start an interactive remote shell.",
                    "Opens an interactive shell over the active client connection. This command takes no arguments.",
                ),
            ),
            config.ControllerType.UPLOAD: contract.RouteRegistration(
                controller.call_upload,
                contract.RouteHelp(
                    "Upload a local file to the remote client.", "Usage: upload <filepath> [destination]. The destination path is optional."
                ),
            ),
            config.ControllerType.EXECUTE: contract.RouteRegistration(
                controller.call_execute,
                contract.RouteHelp(
                    "Execute a local script on the remote client.",
                    "Usage: execute <filepath>. The script is sent from the local system and executed remotely.",
                ),
            ),
            config.ControllerType.EXIT: contract.RouteRegistration(
                controller.call_exit,
                contract.RouteHelp("End the active session.", "Terminates the interactive session gracefully. This command takes no arguments."),
            ),
        }
        enabled_controllers = supported_controllers | {config.ControllerType.HELP, config.ControllerType.EXIT}
        selected_registrations = {kind: registration for kind, registration in registrations.items() if kind in enabled_controllers}
        existing_routes = set(self._router.routes)

        for kind in selected_registrations:
            if kind.value in existing_routes:
                raise config.DuplicateRouteError(kind.value, "route already exists.")

        for kind, registration in selected_registrations.items():
            self._router.connect(kind.value, registration)
