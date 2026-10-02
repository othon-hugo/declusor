from collections.abc import Callable

from declusor import app, contract, core


def run_terminal_app(
    plugin_config: contract.PluginConfig[contract.ParsedArguments],
    *,
    plugin_manager: core.PluginManager | None = None,
    application: core.Application | None = None,
    application_factory: Callable[..., core.Application] | None = None,
) -> int:
    """Compose and run an interactive terminal REPL session.

    Args:
        plugin_config: Validated client plugin configuration.
        plugin_manager: Optional pre-discovered plugin manager.
        application: Optional application instance to execute.
        application_factory: Optional factory producing Application when omitted.

    Returns:
        Process exit code. ``0`` indicates successful completion.
    """

    factory = application_factory or app.create_terminal_application
    active_app = application or factory(plugin_manager=plugin_manager)
    active_app.run(plugin_config)

    return 0
