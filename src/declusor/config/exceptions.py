from pathlib import Path
from typing import Any


class DeclusorException(Exception):
    """Root base exception for all errors raised across Declusor.

    All custom domain exceptions inherit from this class, enabling higher
    layers to catch any framework error using a single unified type.
    """


class DeclusorWarning(Warning):
    """Root base warning for non-fatal diagnostic messages in Declusor."""

    def __init__(self, description: str, /) -> None:
        """Initialize warning with diagnostic description."""

        self.description = description

        super().__init__(self.description)


class ConnectionError(DeclusorException):
    """Raised when an operation on a network connection or transport fails."""


class ConnectionClosed(ConnectionError):
    """Raised when the remote peer gracefully closes or terminates the connection unexpectedly."""

    def __init__(self, message: str = "Connection is closed.", *, peer_address: str | None = None) -> None:
        """Initialize connection closed exception with optional peer address."""

        self.peer_address = peer_address

        super().__init__(message)


class ConnectionTimeoutError(ConnectionError):
    """Raised when a socket read, write, or handshake operation times out."""

    def __init__(
        self,
        message: str,
        *,
        timeout: float | None = None,
        operation: str | None = None,
    ) -> None:
        """Initialize timeout error with operation context and timeout duration."""

        self.timeout = timeout
        self.operation = operation

        super().__init__(message)


class ConnectionHandshakeError(ConnectionError):
    """Raised when the client session initialization handshake or ACK validation fails."""

    def __init__(
        self,
        message: str = "Handshake failed.",
        *,
        expected_ack: bytes | None = None,
        received_ack: bytes | None = None,
    ) -> None:
        """Initialize handshake error with expected and received ACK tokens."""

        self.expected_ack = expected_ack
        self.received_ack = received_ack

        super().__init__(message)


class StorageError(DeclusorException):
    """Base exception for file, directory, or asset storage operations."""

    def __init__(self, message: str, *, path: str | Path | None = None) -> None:
        """Initialize storage error with optional file/directory path context."""

        self.path = Path(path) if path is not None else None

        super().__init__(message)


class InvalidOperation(DeclusorException):
    """Raised when an invalid command operation is requested in the current session."""

    def __init__(self, description: str, /) -> None:
        """Initialize invalid operation with failure description."""

        self.description = description

        super().__init__(f"invalid operation: {self.description}")


class StorageValidationError(StorageError, InvalidOperation):
    """Raised when a storage path or file invariant is violated."""

    def __init__(self, message: str, *, path: str | Path | None = None) -> None:
        """Initialize storage validation error preserving InvalidOperation compatibility."""

        self.path = Path(path) if path is not None else None
        self.description = message

        super().__init__(message, path=self.path)


class CommandError(DeclusorException):
    """Raised when a command fails to prepare, validate, or execute."""

    def __init__(self, description: str, /, *, command_name: str | None = None) -> None:
        """Initialize command error with description and optional command identifier."""

        self.description = description
        self.command_name = command_name

        super().__init__(f"command error: {self.description}")


class CommandValidationError(CommandError, InvalidOperation):
    """Raised when command input parameters or DTO invariants are violated."""

    def __init__(
        self,
        description: str,
        /,
        *,
        field: str | None = None,
        value: Any = None,
        command_name: str | None = None,
    ) -> None:
        """Initialize command validation error with field and value context."""

        self.field = field
        self.value = value

        super().__init__(description, command_name=command_name)


class ControllerError(DeclusorException):
    """Raised when an error occurs during controller dispatch, parameter extraction, or execution."""

    def __init__(self, description: str, /, *, controller_name: str | None = None) -> None:
        """Initialize controller error with failure description and optional controller name."""

        self.description = description
        self.controller_name = controller_name

        super().__init__(f"controller error: {self.description}")


class ParserError(DeclusorException):
    """Raised when command-line argument parsing or configuration validation fails."""


class RouterError(DeclusorException):
    """Raised when a route cannot be found or is invalid in the route table."""

    def __init__(self, route: str, description: str | None = None) -> None:
        """Initialize router error with route identifier and optional description."""

        self.route = route
        self.description = description

        msg = f"invalid route: {route!r}" + (f" ({description})" if description else "")

        super().__init__(msg)


class DuplicateRouteError(RouterError, ValueError):
    """Raised when attempting to register a route that already exists in the route table."""

    def __init__(self, route: str, description: str = "route already exists.") -> None:
        """Initialize duplicate route error maintaining ValueError backward-compatibility."""

        super().__init__(route, description)


class PluginError(DeclusorException):
    """Base exception for client plugin discovery, loading, and runtime errors."""

    def __init__(self, message: str, *, plugin_name: str | None = None) -> None:
        """Initialize plugin error with failure message and optional plugin name."""

        self.plugin_name = plugin_name

        super().__init__(message)


class PluginNotFoundError(PluginError):
    """Raised when a requested client plugin is not registered or discovered."""

    def __init__(
        self,
        plugin_name: str,
        available_plugins: tuple[str, ...] | list[str] = (),
        message: str | None = None,
    ) -> None:
        """Initialize plugin not found error with available plugins context."""

        self.available_plugins = tuple(available_plugins)
        available_str = ", ".join(repr(k) for k in sorted(self.available_plugins)) or "none"
        msg = message or f"Unknown client {plugin_name!r}. Available clients: {available_str}"

        super().__init__(msg, plugin_name=plugin_name)


class PluginValidationError(PluginError):
    """Raised when a candidate plugin fails contract validation during discovery or registration."""

    def __init__(
        self,
        message: str,
        *,
        plugin_name: str | None = None,
        candidate: type | None = None,
    ) -> None:
        """Initialize plugin validation error with candidate type context."""

        self.candidate = candidate

        super().__init__(message, plugin_name=plugin_name)


class LauncherDeliveryError(PluginError):
    """Raised when rendering or writing a client launcher script delivery envelope fails."""

    def __init__(
        self,
        message: str,
        *,
        output_path: Path | str | None = None,
        plugin_name: str | None = None,
    ) -> None:
        """Initialize launcher delivery error with destination path context."""

        self.output_path = Path(output_path) if output_path is not None else None

        super().__init__(message, plugin_name=plugin_name)


class PromptError(DeclusorException):
    """Raised when an interactive prompt command or argument is invalid or malformed."""

    def __init__(self, argument: str, description: str | None = None) -> None:
        """Initialize prompt error with argument token and optional description."""

        self.argument = argument
        self.description = description

        msg = f"invalid argument: {argument!r}" + (f" ({description})" if description else "")

        super().__init__(msg)
