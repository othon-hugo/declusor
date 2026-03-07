from typing import Callable, NoReturn, Type

from declusor import config


def handle_exception(exc: BaseException) -> NoReturn:
    """Handle exceptions and exit the program with an appropriate message."""

    handler_table: dict[Type[BaseException], Callable[[BaseException], str]] = {
        config.ConnectionFailure: lambda e: str(e),
        FileNotFoundError: lambda e: f"file or directory not found: {e}",
        NotADirectoryError: lambda e: f"not a directory: {e}",
        OSError: lambda e: str(e),
    }

    for exception_type, get_message in handler_table.items():
        if isinstance(exc, exception_type):
            sysexit = SystemExit(get_message(exc))
            sysexit.code = 1

            raise sysexit

    raise exc
