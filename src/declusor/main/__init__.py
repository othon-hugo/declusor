from declusor import config, core
from declusor.main import exception, service

__all__ = ["main"]


def main() -> None:
    """Main entry point for the Declusor application."""

    router = core.Router()

    try:
        options = core.DeclusorParser(config.Settings.PROJECT_NAME, description=config.Settings.PROJECT_DESCRIPTION).parse()
    except config.ParserError as e:
        raise SystemExit(f"parser error: {e}")

    console = core.Console()

    try:
        service.run_service(router, console, options)
    except KeyboardInterrupt:
        print()
    except config.DeclusorException as e:
        exception.handle_exception(e)
