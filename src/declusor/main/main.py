import sys
from collections.abc import Sequence

from declusor.main.terminal import RunnableApplication, run_terminal_app


def main(
    argv: Sequence[str] | None = None,
    application: RunnableApplication | None = None,
) -> int:
    """Main application composition root and entry point.

    Delegates execution to the configured view/mode runner.

    Args:
        argv: Optional command-line arguments. Defaults to sys.argv[1:].
        application: Optional application instance for test injection.

    Returns:
        Process exit code. ``0`` for success, ``1`` for runtime error, ``2`` for usage error.
    """

    args = list(argv) if argv is not None else sys.argv[1:]

    return run_terminal_app(args, application=application)
