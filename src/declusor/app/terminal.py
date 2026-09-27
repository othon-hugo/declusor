from collections.abc import Sequence
from pathlib import Path

from declusor import config, contract, core, presentation


class TerminalApplication[T: contract.ParsedArguments](core.Application[T]):
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
    ) -> None:
        """Create a TerminalApplication with terminal view, input source, and prompt loop.

        Args:
            manager: Plugin manager containing the available client plugins.
            router: Command router resolving interactive prompt input to controller actions.
            view: Operator view interface handling output presentation.
            input_source: Operator input source interface reading commands.
            runner: Optional session runner. Defaults to PromptLoop.
        """

        super().__init__(
            router,
            view,
            plugin_manager=plugin_manager,
            session_runner=session_runner,
            input_source=input_source,
        )


def create_terminal_application(
    search_dirs: Sequence[Path] | None = None,
) -> TerminalApplication[contract.ParsedArguments]:
    """Create a TerminalApplication with discovered plugins and terminal components.

    Args:
        search_dirs: Optional sequence of paths to search for plugins.

    Returns:
        Fully composed TerminalApplication ready to execute.
    """

    router = core.Router()
    view = presentation.TerminalView()
    plugin_manager = core.PluginManager().discover(search_dirs)
    session_runner = presentation.PromptLoop(config.Settings.PROJECT_NAME)
    input_source = presentation.TerminalInputSource()

    return TerminalApplication(
        router,
        view,
        plugin_manager=plugin_manager,
        session_runner=session_runner,
        input_source=input_source,
    )
