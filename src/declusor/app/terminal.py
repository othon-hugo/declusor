from collections.abc import Callable, Sequence
from pathlib import Path

from declusor import config, contract, core, presentation, transport


class TerminalApplication(core.Application):
    """Specialized application pre-configured for interactive terminal REPL."""

    def __init__(
        self,
        router: contract.IRouter,
        view: contract.IView,
        /,
        *,
        plugin_manager: core.PluginManager,
        session_runner: contract.ISessionRunner,
        input_source: contract.IInputSource | None = None,
        listener_factory: Callable[[str, int], contract.ITransportListener] | None = None,
        launcher_renderer: core.LauncherRenderer | None = None,
        transport_registry: transport.TransportLayerRegistry | None = None,
    ) -> None:
        """Create a TerminalApplication with terminal view, input source, and prompt loop.

        Args:
            router: Command router resolving interactive prompt input to controller actions.
            view: Operator view interface handling output presentation.
            plugin_manager: Plugin manager containing the available client plugins.
            session_runner: Session runner executing interaction workflows over active sessions.
            input_source: Operator input source interface reading commands.
            listener_factory: Optional factory producing an ITransportListener for network connections.
            launcher_renderer: Optional renderer responsible for delivering client launcher.
            transport_registry: Optional registry managing composable transport layers.
        """

        super().__init__(
            router,
            view,
            plugin_manager=plugin_manager,
            session_runner=session_runner,
            input_source=input_source,
            listener_factory=listener_factory,
            launcher_renderer=launcher_renderer,
            transport_registry=transport_registry,
        )


def create_terminal_application(
    search_dirs: Sequence[Path] | None = None,
    *,
    plugin_manager: core.PluginManager | None = None,
    transport_registry: transport.TransportLayerRegistry | None = None,
    listener_factory: Callable[[str, int], contract.ITransportListener] | None = None,
    launcher_renderer: core.LauncherRenderer | None = None,
    router: contract.IRouter | None = None,
    view: contract.IView | None = None,
    input_source: contract.IInputSource | None = None,
    session_runner: contract.ISessionRunner | None = None,
) -> TerminalApplication:
    """Create a TerminalApplication with discovered plugins and terminal components.

    Args:
        search_dirs: Optional sequence of paths to search for plugins.
        plugin_manager: Optional existing plugin manager instance.
        transport_registry: Optional transport layer registry instance.
        listener_factory: Optional factory producing an ITransportListener for network connections.
        launcher_renderer: Optional renderer responsible for delivering client launcher.
        router: Optional command router instance.
        view: Optional presentation view interface.
        input_source: Optional input source interface.
        session_runner: Optional session runner executing interaction workflows.

    Returns:
        Fully composed TerminalApplication ready to execute.
    """

    active_router = router or core.Router()
    active_view = view or presentation.TerminalView()
    manager = plugin_manager or core.PluginManager().discover(search_dirs)
    active_session_runner = session_runner or presentation.PromptLoop(config.PROJECT_NAME)
    active_input_source = input_source or presentation.TerminalInputSource()

    return TerminalApplication(
        active_router,
        active_view,
        plugin_manager=manager,
        session_runner=active_session_runner,
        input_source=active_input_source,
        listener_factory=listener_factory,
        launcher_renderer=launcher_renderer,
        transport_registry=transport_registry,
    )
