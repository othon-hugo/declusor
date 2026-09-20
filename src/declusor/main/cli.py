import sys
from collections.abc import Sequence

from declusor import app, config, core


def main(
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

    declusor_parser = core.DeclusorParser(
        name=config.Settings.PROJECT_NAME,
        description=config.Settings.PROJECT_DESCRIPTION,
    )

    try:
        if application is None:
            preliminary_args, _ = declusor_parser.parse_known_args(argv)
            mode = getattr(preliminary_args, "mode", config.Settings.DEFAULT_EXECUTION_MODE)
            declusor_app = app.create_application(mode=mode)
        else:
            declusor_app = application

        plugin_config = declusor_parser.parse(declusor_app.manager, argv)
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
