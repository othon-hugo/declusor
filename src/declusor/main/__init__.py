from declusor import config, core
from declusor.main.exception import handle_exception
from declusor.main.service import register_plugins, run_service, validate_directories

__all__ = [
    "main",
    "register_plugins",
    "run_service",
    "validate_directories",
]


def main() -> None:
    """Main entry point for the Declusor application."""

    register_plugins(core.ClientRegistry)

    router = core.Router()

    try:
        options = core.DeclusorParser(config.Settings.PROJECT_NAME, description=config.Settings.PROJECT_DESCRIPTION).parse()
    except config.ParserError as e:
        raise SystemExit(f"parser error: {e}") from e

    console = core.Console()

    try:
        run_service(router, console, options)
    except KeyboardInterrupt:
        print()
    except config.DeclusorException as e:
        handle_exception(e)
