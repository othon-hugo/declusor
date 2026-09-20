from collections.abc import Sequence
from sys import stderr

from declusor import config
from declusor.main.app import create_application


def main(argv: Sequence[str] | None = None) -> int:
    """Run Declusor from command-line arguments.

    Args:
        argv: Arguments to parse, excluding the executable name. When ``None``,
            arguments are read from the process command line.

    Returns:
        Process exit code. ``0`` indicates successful completion.
    """

    application = create_application()

    try:
        options = application.parse(argv)
        application.run(options)
    except KeyboardInterrupt:
        print()
    except config.ParserError as error:
        print(f"parser error: {error}", file=stderr)
        return 2
    except config.DeclusorException as error:
        print(f"declusor error: {error}", file=stderr)
        return 1

    return 0
