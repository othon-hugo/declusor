"""Application flavors package encapsulating target execution runtimes."""

from .terminal import (
    TerminalApplication,
    create_terminal_application,
)

__all__ = [
    "create_terminal_application",
    "TerminalApplication",
]
