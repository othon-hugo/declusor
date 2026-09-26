from abc import ABC, abstractmethod


class IInputSource(ABC):
    """Contract for reading operator input in Declusor.

    Implementations provide input from their specific medium (readline
    terminal, HTTP request queue, MCP tool invocation). Test doubles
    manage an in-memory input queue.
    """

    @abstractmethod
    def read_command(self, prompt: str = "", /) -> str:
        """Read a command string from the operator.

        Blocks until input is available. Returns the stripped, non-empty
        command string. Implementations decide how to handle prompting.

        Args:
            prompt: Text prompt displayed to the operator before input.

        Returns:
            The stripped command string entered by the operator.
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
