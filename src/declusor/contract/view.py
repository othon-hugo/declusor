from abc import ABC, abstractmethod


class IView(ABC):
    """Contract for all output presentation in Declusor.

    Implementations render operator-facing output through their specific
    medium (terminal, API response, MCP tool result). Test doubles capture
    output without side effects.
    """

    @abstractmethod
    def write_message(self, message: str, /) -> None:
        """Display a plain informational message.

        Args:
            message: The message string to display.
        """

        raise NotImplementedError

    @abstractmethod
    def write_error(self, message: str | BaseException, /) -> None:
        """Display an error-level message.

        Args:
            message: Error description or exception to display.
        """

        raise NotImplementedError

    @abstractmethod
    def write_warning(self, message: str | BaseException, /) -> None:
        """Display a warning-level message.

        Args:
            message: Warning description or exception to display.
        """

        raise NotImplementedError

    @abstractmethod
    def write_info(self, message: str, /) -> None:
        """Display an informational notice.

        Args:
            message: Informational text to display.
        """

        raise NotImplementedError

    @abstractmethod
    def write_success(self, message: str, /) -> None:
        """Display a success confirmation.

        Args:
            message: Success text to display.
        """

        raise NotImplementedError

    @abstractmethod
    def write_binary_data(self, data: bytes, /) -> None:
        """Write raw bytes to the output stream.

        Args:
            data: Binary payload to write verbatim.
        """

        raise NotImplementedError
