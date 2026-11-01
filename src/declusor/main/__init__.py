"""Main package serving as the composition root and CLI entry point."""

from .main import (
    run,
)
from .terminal import (
    run_terminal_app,
)

__all__ = [
    "run_terminal_app",
    "run",
]
