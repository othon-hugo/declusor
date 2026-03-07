from abc import ABC, abstractmethod
from pathlib import Path
from typing import Sequence


class IConsole(ABC):
    """Abstract base class defining the console interface for input reading."""

    @abstractmethod
    def setup_completer(self, commands: Sequence[str], /) -> None:
        """Set up the readline completer for command line input.

        Args:
            commands: Sequence of available commands.
        """

        raise NotImplementedError

    @abstractmethod
    def enable_history(self, history_file: Path, /) -> None:
        """Enable history saving and loading.

        Args:
            history_file: Path to the history file.
        """

        raise NotImplementedError

    @abstractmethod
    def read_line(self, prompt: str = "", /) -> str:
        """Read a line from standard input.

        Args:
            prompt: The prompt to display to the user.

        Returns:
            The input string.
        """

        raise NotImplementedError

    @abstractmethod
    def read_stripped_line(self, prompt: str = "", /) -> str:
        """Read a line from standard input and strip whitespace.

        Args:
            prompt: The prompt to display to the user.

        Returns:
            The stripped input string.
        """

        raise NotImplementedError

    @abstractmethod
    def write_message(self, message: str, /) -> None:
        """Write a message to standard output.

        Args:
            message: The message string to write.
        """

        raise NotImplementedError

    @abstractmethod
    def write_binary_data(self, message: bytes, /) -> None:
        """Write binary data to standard output.

        Args:
            message: The binary data to write.
        """

        raise NotImplementedError

    @abstractmethod
    def write_error_message(self, message: str | BaseException, /) -> None:
        """Write an error message to standard error.

        Args:
            message: The error message or exception to write.
        """

        raise NotImplementedError

    @abstractmethod
    def write_warning_message(self, message: str | BaseException, /) -> None:
        """Write a warning message to standard error.

        Args:
            message: The warning message or exception to write.
        """

        raise NotImplementedError
