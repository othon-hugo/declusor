from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from declusor.contract.connection import IConnection
    from declusor.contract.console import IConsole

Controller = Callable[["IConnection", "IConsole", str], None]
"""Type alias for a controller function.

A controller receives an active connection, a console for operator I/O,
and the raw argument string from the command line.
"""
