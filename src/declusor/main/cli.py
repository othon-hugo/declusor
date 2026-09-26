import sys
from collections.abc import Sequence

from declusor import config, core

from .application import ApplicationProtocol
from .terminal import create_terminal_application


def main(
    argv: Sequence[str] | None = None,
    application: ApplicationProtocol | None = None,
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

    app = application if application is not None else create_terminal_application()
    parser = core.DeclusorParser(
        app.manager,
        name=config.Settings.PROJECT_NAME,
        description=config.Settings.PROJECT_DESCRIPTION,
    )

    try:
        plugin_config = parser.parse(argv)
        app.run(plugin_config)
    except KeyboardInterrupt:
        print()
    except config.ParserError as error:
        print(f"parser error: {error}", file=sys.stderr)
        return 2
    except config.DeclusorException as error:
        print(f"declusor error: {error}", file=sys.stderr)
        return 1

    return 0
