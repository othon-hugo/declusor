from typing import Callable, NoReturn, Type

from declusor import config


def handle_exception(exc: BaseException) -> NoReturn:
    """Convert a known exception into a ``SystemExit`` with a user-friendly message.

    Walks a priority-ordered handler table; the first matching type wins.
    Unrecognised exceptions are re-raised as-is (preserving stack trace).

    Args:
        exc: The exception to handle.

    Raises:
        SystemExit: With exit code 1 and a descriptive message for known types.
        BaseException: Re-raises *exc* unchanged if no handler matches.
    """

    handler_table: dict[Type[BaseException], Callable[[BaseException], str]] = {
        config.ConnectionFailure: lambda e: f"failed to connect to database: {e}",
        FileNotFoundError: lambda e: f"file or directory not found: {e}",
        NotADirectoryError: lambda e: f"not a directory: {e}",
        OSError: lambda e: f"operating system error: {e}",
    }

    for exception_type, get_message in handler_table.items():
        if isinstance(exc, exception_type):
            sysexit = SystemExit(get_message(exc))
            sysexit.code = 1

            raise sysexit

    raise exc
