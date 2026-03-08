from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from declusor.interface.connection import IConnection
    from declusor.interface.console import IConsole

Controller = Callable[["IConnection", "IConsole", str], None]
"""Type alias for a controller function.

A controller receives an active connection, a console for operator I/O,
and the raw argument string from the command line.
"""
