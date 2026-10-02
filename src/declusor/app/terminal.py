from collections.abc import Sequence
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
            launcher_renderer: Optional renderer responsible for delivering client launcher.
            transport_registry: Optional registry managing composable transport layers.
        """

        super().__init__(
            router,
            view,
            plugin_manager=plugin_manager,
            session_runner=session_runner,
            input_source=input_source,
            launcher_renderer=launcher_renderer,
            transport_registry=transport_registry,
        )


def create_terminal_application(
    search_dirs: Sequence[Path] | None = None,
    *,
    plugin_manager: core.PluginManager | None = None,
    transport_registry: transport.TransportLayerRegistry | None = None,
) -> TerminalApplication:
    """Create a TerminalApplication with discovered plugins and terminal components.

    Args:
        search_dirs: Optional sequence of paths to search for plugins.
        plugin_manager: Optional existing plugin manager instance.
        transport_registry: Optional transport layer registry instance.

    Returns:
        Fully composed TerminalApplication ready to execute.
    """

    router = core.Router()
    view = presentation.TerminalView()
    manager = plugin_manager or core.PluginManager().discover(search_dirs)
    session_runner = presentation.PromptLoop(config.PROJECT_NAME)
    input_source = presentation.TerminalInputSource()

    return TerminalApplication(
        router,
        view,
        plugin_manager=manager,
        session_runner=session_runner,
        input_source=input_source,
        transport_registry=transport_registry,
    )
