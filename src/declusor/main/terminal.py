from collections.abc import Sequence
from pathlib import Path

from declusor import config, contract, core, presentation

from .application import Application


class TerminalApplication(Application):
    """Specialized application pre-configured for interactive terminal REPL."""

    def __init__(
        self,
        manager: core.PluginManager,
        router: contract.IRouter,
        view: contract.IView,
        input_source: contract.IInputSource,
        runner: contract.ISessionRunner | None = None,
        /,
    ) -> None:
        """Create a TerminalApplication with terminal view, input source, and prompt loop.

        Args:
            manager: Plugin manager containing the available client plugins.
            router: Command router resolving interactive prompt input to controller actions.
            view: Operator view interface handling output presentation.
            input_source: Operator input source interface reading commands.
            runner: Optional session runner. Defaults to PromptLoop.
        """

        terminal_runner = runner if runner is not None else presentation.PromptLoop(config.Settings.PROJECT_NAME)
        super().__init__(manager, router, view, terminal_runner, input_source)


def create_terminal_application(search_dirs: Sequence[Path] | None = None) -> TerminalApplication:
    """Create a TerminalApplication with discovered plugins and terminal components.

    Args:
        search_dirs: Optional sequence of paths to search for plugins.

    Returns:
        Fully composed TerminalApplication ready to execute.
    """

    manager = core.PluginManager().discover(search_dirs)
    router = core.Router()
    view = presentation.TerminalView()
    input_source = presentation.TerminalInputSource()

    return TerminalApplication(manager, router, view, input_source)


def create_application(search_dirs: Sequence[Path] | None = None) -> TerminalApplication:
    """Create a default Declusor application (TerminalApplication).

    Args:
        search_dirs: Optional sequence of paths to search for plugins.

    Returns:
        Fully composed TerminalApplication ready to execute parsed options.
    """

    return create_terminal_application(search_dirs)
