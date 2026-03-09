from declusor import config, cli, routing
from declusor.main import exception, service

__all__ = ["main"]


def main() -> None:
    """Main entry point for the Declusor application."""

    router = routing.Router()

    try:
        options = cli.DeclusorParser(config.Settings.PROJECT_NAME, description=config.Settings.PROJECT_DESCRIPTION).parse()
    except config.ParserError as e:
        raise SystemExit(f"parser error: {e}") from e

    console = cli.Console()

    try:
        service.run_service(router, console, options)
    except KeyboardInterrupt:
        print()
    except config.DeclusorException as e:
        exception.handle_exception(e)
