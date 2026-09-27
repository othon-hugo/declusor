import sys
from collections.abc import Sequence
from pathlib import Path

from declusor import config, contract, core


def _default_cli_factory(search_dirs: Sequence[Path] | None = None) -> core.ApplicationProtocol:
    """Instantiate the default terminal application, respecting module monkeypatching in tests."""

    app_module = sys.modules.get("declusor.app")

    if app_module is not None and hasattr(app_module, "create_terminal_application"):
        factory = app_module.create_terminal_application

        if factory is not _default_cli_factory:
            return factory(search_dirs)  # type: ignore[no-any-return]

    from declusor.app.terminal import create_terminal_application

    return create_terminal_application(search_dirs)


_APPLICATION_FACTORIES: dict[config.ExecutionMode, contract.ApplicationFactory] = {
    config.ExecutionMode.CLI: _default_cli_factory,
}


def register_application_factory(mode: config.ExecutionMode, factory: contract.ApplicationFactory) -> None:
    """Register or replace an application factory for a specific execution mode.

    Args:
        mode: Execution mode to register.
        factory: Callable accepting search_dirs and returning an ApplicationProtocol.
    """

    _APPLICATION_FACTORIES[mode] = factory


def get_application_factory(mode: config.ExecutionMode) -> contract.ApplicationFactory:
    """Retrieve the application factory for an execution mode.

    Args:
        mode: Target execution mode.

    Returns:
        The registered factory callable.

    Raises:
        InvalidOperation: If no factory is registered for the specified mode.
    """

    factory = _APPLICATION_FACTORIES.get(mode)

    if factory is None:
        raise config.InvalidOperation(f"Execution mode '{mode.value}' is not supported yet or has no registered application factory.")

    return factory


def create_application(
    mode: config.ExecutionMode = config.Settings.DEFAULT_EXECUTION_MODE,
    search_dirs: Sequence[Path] | None = None,
) -> core.ApplicationProtocol:
    """Create an application instance for the specified execution mode.

    Args:
        mode: Target execution mode. Defaults to Settings.DEFAULT_EXECUTION_MODE (CLI).
        search_dirs: Optional sequence of paths to search for plugins.

    Returns:
        Configured application instance conforming to ApplicationProtocol.
    """

    factory = get_application_factory(mode)

    return factory(search_dirs)
