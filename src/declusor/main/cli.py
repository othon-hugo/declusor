import sys
from collections.abc import Sequence

from declusor import app, config, core


def run(
    argv: Sequence[str] | None = None,
    application: core.ApplicationProtocol | None = None,
) -> int:
    """Run Declusor from command-line arguments.

    Args:
        argv: Arguments to parse, excluding the executable name. When ``None``,
            arguments are read from the process command line.
        application: Optional application instance to execute. Defaults to
            a fresh ``TerminalApplication``.

    Returns:
        Process exit code. ``0`` indicates successful completion.
    """

    declusor_app = application or app.create_terminal_application()
    declusor_parser = core.DeclusorParser(
        declusor_app.manager,
        name=config.Settings.PROJECT_NAME,
        description=config.Settings.PROJECT_DESCRIPTION,
    )

    try:
        plugin_config = declusor_parser.parse(argv)
        declusor_app.run(plugin_config)
    except KeyboardInterrupt:
        print()
    except config.ParserError as error:
        print(f"parser error: {error}", file=sys.stderr)
        return 2
    except config.DeclusorException as error:
        print(f"declusor error: {error}", file=sys.stderr)
        return 1

    return 0
