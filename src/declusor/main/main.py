import sys
from collections.abc import Callable, Sequence

from declusor import config, core
from declusor.main.terminal import run_terminal_app


def main(
    argv: Sequence[str] | None = None,
    *,
    application: core.Application | None = None,
    plugin_manager: core.PluginManager | None = None,
    application_factory: Callable[..., core.Application] | None = None,
) -> int:
    """Main application composition root and entry point.

    Discovers plugins, parses command-line arguments via DeclusorParser,
    delegates execution to the configured view/mode runner, and maps exceptions
    to deterministic process exit codes (0, 1, 2).

    Args:
        argv: Optional command-line argument list. Defaults to sys.argv[1:].
        application: Optional application instance for test injection.
        plugin_manager: Optional pre-configured plugin manager instance.
        application_factory: Optional factory creating Application when omitted.

    Returns:
        Process exit code. ``0`` for success, ``1`` for runtime error, ``2`` for usage error.
    """

    args = list(argv) if argv is not None else sys.argv[1:]

    try:
        manager = plugin_manager or (application.plugin_manager if application is not None else core.PluginManager().discover())
        parser = core.DeclusorParser(
            config.PROJECT_NAME,
            config.PROJECT_DESCRIPTION,
        )
        plugin_config = parser.parse(manager, args)

        match plugin_config.mode:
            case config.ExecutionMode.CLI:
                return run_terminal_app(
                    plugin_config,
                    plugin_manager=manager,
                    application=application,
                    application_factory=application_factory,
                )
            case _:
                print(
                    f"Execution mode '{plugin_config.mode.value}' is not supported yet.",
                    file=sys.stderr,
                )
                return 1

    except config.ParserError as error:
        print(f"parser error: {error}", file=sys.stderr)
        return 2

    except config.DeclusorException as error:
        print(f"declusor error: {error}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        return 0
