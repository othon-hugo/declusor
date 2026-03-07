from abc import ABC, abstractmethod
from pathlib import Path
from typing import Sequence


class IConsole(ABC):
    """Contract for all console I/O in Declusor.

    Implementations supply the concrete I/O backend (e.g. ``sys.stdout`` /
    ``input()``). Test doubles implement this interface to capture output
    without writing to real file descriptors.
    """

    @abstractmethod
    def setup_completer(self, commands: Sequence[str], /) -> None:
        """Configure tab-completion for the readline interface.

        Args:
            commands: The set of top-level command names to offer as completions.
        """

        raise NotImplementedError

    @abstractmethod
    def enable_history(self, history_file: Path, /) -> None:
        """Load history from *history_file* and persist it on exit.

        Args:
            history_file: Path to the readline history file. Created if absent.
        """

        raise NotImplementedError

    @abstractmethod
    def read_line(self, prompt: str = "", /) -> str:
        """Read a single line of input from the user.

        Args:
            prompt: Text displayed before the cursor. Defaults to no prompt.

        Returns:
            The raw input string, including any surrounding whitespace.
        """

        raise NotImplementedError

    @abstractmethod
    def read_stripped_line(self, prompt: str = "", /) -> str:
        """Read a line of input from the user with leading/trailing whitespace removed.

        Args:
            prompt: Text displayed before the cursor. Defaults to no prompt.

        Returns:
            The input string with leading and trailing whitespace stripped.
        """

        raise NotImplementedError

    @abstractmethod
    def write_message(self, message: str, /) -> None:
        """Write a plain-text message to the standard output stream.

        Args:
            message: The string to display.
        """

        raise NotImplementedError

    @abstractmethod
    def write_binary_data(self, message: bytes, /) -> None:
        """Write raw bytes to the standard output buffer.

        Args:
            message: Binary data to write verbatim (no encoding applied).
        """

        raise NotImplementedError

    @abstractmethod
    def write_error_message(self, message: str | BaseException, /) -> None:
        """Write an error-prefixed message to standard error.

        Args:
            message: Error description or exception to display.
        """

        raise NotImplementedError

    @abstractmethod
    def write_warning_message(self, message: str | BaseException, /) -> None:
        """Write a warning-prefixed message to standard error.

        Args:
            message: Warning description or exception to display.
        """

        raise NotImplementedError
