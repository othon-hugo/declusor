import sys
from collections.abc import Sequence
from typing import Protocol

from declusor import app, config, contract, core


class RunnableApplication(Protocol):
    """Protocol for applications runnable with a PluginConfig."""

    def run(self, config: contract.PluginConfig[contract.ParsedArguments], /) -> None:
        """Execute the application with the given plugin configuration."""
        ...


def run_terminal_app(
    argv: Sequence[str] | None = None,
    /,
    *,
    plugin_config: contract.PluginConfig[contract.ParsedArguments] | None = None,
    application: RunnableApplication | None = None,
    plugin_manager: core.PluginManager | None = None,
) -> int:
    """Compose and run an interactive terminal REPL session.

    Args:
        argv: Optional command-line argument list.
        plugin_config: Optional pre-parsed client plugin configuration.
        application: Optional application instance to execute.
        plugin_manager: Optional pre-discovered plugin manager.

    Returns:
        Process exit code. ``0`` indicates successful completion.
    """

    declusor_parser = core.DeclusorParser(
        name=config.Settings.PROJECT_NAME,
        description=config.Settings.PROJECT_DESCRIPTION,
    )

    try:
        manager = (
            getattr(application, "manager", None) or getattr(application, "plugin_manager", None) or plugin_manager or core.PluginManager().discover()
        )

        resolved_config = plugin_config or declusor_parser.parse(manager, argv)

        if resolved_config.mode != config.ExecutionMode.CLI:
            print(
                f"Execution mode '{resolved_config.mode.value}' is not supported yet.",
                file=sys.stderr,
            )
            return 1

        active_app = application or app.create_terminal_application(plugin_manager=manager)
        active_app.run(resolved_config)

    except config.ParserError as error:
        print(f"parser error: {error}", file=sys.stderr)
        return 2

    except config.DeclusorException as error:
        print(f"declusor error: {error}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        return 0

    return 0
