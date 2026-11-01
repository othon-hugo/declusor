"""Operator input source contracts, readline abstractions, and prompt providers."""

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from pathlib import Path

from declusor import config


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
