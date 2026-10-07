import dataclasses
from collections.abc import Callable
from typing import TYPE_CHECKING

from declusor import config, contract, transport

from .launcher import LauncherRenderer
from .routes import EXIT_ROUTE, OFFICIAL_ROUTES, create_help_route

if TYPE_CHECKING:
    from .plugin import PluginManager

type TransportListenerFactory = Callable[[str, int], contract.ITransportListener]
"""Factory for creating a transport listener bound to a host and port."""


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
            plugin: Plugin class implementing ``IPluginExtension``.
        """

        self._plugin_manager.register(plugin)

    def run(self, plugin_config: contract.PluginConfig[contract.ParsedArguments], /) -> None:
        """Run the configured server connection.

        Args:
            plugin_config: Validated client plugin configuration.

        Raises:
            PluginNotFoundError: If the configured plugin kind is not registered.
            PluginValidationError: If plugin routes are invalid or protected routes are overridden.
            DuplicateRouteError: If a composed route already exists in the router.
            InvalidOperation: If this application was already configured for a different plugin.
            ConnectionError: If listener, transport, or handshake setup fails.
        """

        PluginExtension = self._plugin_manager.get(plugin_config.kind)

        if self._route_plugin_name is None:
            self._connect_routes(PluginExtension.routes)
            self._route_plugin_name = PluginExtension.name
        elif self._route_plugin_name != PluginExtension.name:
            raise config.InvalidOperation(
                f"Application routes are already configured for plugin {self._route_plugin_name!r}."
                f"Create a new Application to use {PluginExtension.name!r}."
            )

        plugin_runtime = PluginExtension.build_runtime(plugin_config)

        if self._input_source is not None and (setup_completer := getattr(self._input_source, "setup_completer", None)):
            setup_completer(self._router.routes, plugin_config.filesystem.assets)

        delivery = plugin_runtime.launcher
        delivery = dataclasses.replace(
            delivery,
            output_mode=plugin_config.launcher_output_mode,
            output_path=plugin_config.launcher_output_path,
            wrapper_template=plugin_config.launcher_wrapper or delivery.wrapper_template,
        )

        self._launcher_renderer.render(delivery)

        with self._listener_factory(plugin_config.host, plugin_config.port) as listener:
            incoming_transport = listener.accept()

            pipeline = self._transport_registry.build_pipeline(plugin_config.transport_layers)
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

    def _connect_routes(self, plugin_routes: contract.RouteTable, /) -> None:
        """Compose official routes with plugin routes and register the result."""

        registrations = {"help": create_help_route(self._router), **OFFICIAL_ROUTES, "exit": EXIT_ROUTE}

        for route, registration in plugin_routes.items():
            if route in {"help", "exit"}:
                raise config.PluginValidationError(f"Plugins cannot override protected route {route!r}.")

            registrations[route] = registration

        normalized_registrations: dict[str, contract.RouteRegistration] = {}

        for route, registration in registrations.items():
            if not isinstance(route, str) or not route.strip():
                raise config.PluginValidationError("Route names must be non-empty strings.")

            normalized_route = route.strip()

            if normalized_route in normalized_registrations:
                raise config.PluginValidationError(f"Duplicate route after normalization: {normalized_route!r}.")

            if not isinstance(registration, contract.RouteRegistration):
                raise config.PluginValidationError(f"Route {normalized_route!r} must be a RouteRegistration.")

            normalized_registrations[normalized_route] = registration

        existing_routes = {route.strip() for route in self._router.routes}

        for route in normalized_registrations:
            if route in existing_routes:
                raise config.DuplicateRouteError(route, "route already exists.")

        for route, registration in normalized_registrations.items():
            self._router.connect(route, registration)
