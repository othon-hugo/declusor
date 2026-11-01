"""Operator input source contracts, readline abstractions, and prompt providers."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Protocol

from declusor import config


class IReadlineAdapter(Protocol):
    """Abstraction over terminal readline operations for deterministic testing."""

    @property
    def is_available(self) -> bool:
        """Return True when an underlying readline implementation is available."""
        ...

    def get_line_buffer(self) -> str:
        """Return the current contents of the readline line buffer."""
        ...

    def get_completer(self) -> Callable[[str, int], str | None] | None:
        """Return the currently registered completer callable."""
        ...

    def get_completer_delims(self) -> str:
        """Return the word delimiters used for tab completion."""
        ...

    def set_completer(self, completer: Callable[[str, int], str | None] | None = None, /) -> None:
        """Set the readline completer function."""
        ...

    def set_completer_delims(self, string: str, /) -> None:
        """Set the word delimiters for tab completion."""
        ...

    def parse_and_bind(self, line: str, /) -> None:
        """Execute a readline initialization line."""
        ...

    def read_history_file(self, filename: str, /) -> None:
        """Load a readline history file from disk."""
        ...

    def write_history_file(self, filename: str, /) -> None:
        """Write the readline history buffer to disk."""
        ...


class IInputSource(ABC):
    """Contract for reading operator input in Declusor.

    Implementations provide input from their specific medium (readline
    terminal, HTTP request queue, MCP tool invocation). Test doubles
    manage an in-memory input queue.
    """

    @abstractmethod
    def setup_completer(
        self,
        command_routes: Sequence[str],
        assets_dir: Path | None = None,
        route_completions: Mapping[str, config.RouteCompletionMode] | None = None,
        /,
    ) -> None:
        """Configure autocompletion for interactive command-line sessions.

        Args:
            command_routes: Available command route identifiers for autocomplete.
            assets_dir: Optional base directory for completing file and module paths.
            route_completions: Optional mapping of route identifiers to their completion mode.
        """

        raise NotImplementedError

    @abstractmethod
    def read_command(self, prompt: str = "", /) -> str:
        """Read a command string from the operator.

        Requests a command from the input medium and returns it with leading
        and trailing whitespace removed. A blank input may therefore produce
        an empty string. Implementations decide how to handle prompting.

        Args:
            prompt: Text prompt displayed to the operator before input.

        Returns:
            The stripped command string, which may be empty.
        """

        raise NotImplementedError

    @abstractmethod
    def read_raw(self, prompt: str = "", /) -> str:
        """Read a raw line of input without stripping.

        Used by interactive shell mode to forward keystrokes verbatim.
        Returns the raw string including any trailing newline.

        Args:
            prompt: Text prompt displayed to the operator before input.

        Returns:
            The raw string input including trailing newline.
        """

        raise NotImplementedError
