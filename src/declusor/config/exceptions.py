class DeclusorException(Exception):
    """Root base exception for all errors raised across Declusor.

    All custom domain exceptions inherit from this class, enabling higher
    layers to catch any framework error using a single unified type.
    """


class DeclusorWarning(Warning):
    """Root base warning for non-fatal diagnostic messages in Declusor."""

    def __init__(self, description: str, /) -> None:
        self.description = description

        super().__init__(self.description)


class ConnectionError(DeclusorException):
    """Raised when an operation on a network connection or transport fails."""


class ConnectionClosed(ConnectionError):
    """Raised when the remote peer gracefully closes or terminates the connection unexpectedly."""


class ConnectionTimeoutError(ConnectionError):
    """Raised when a socket read, write, or handshake operation times out."""


class ConnectionHandshakeError(ConnectionError):
    """Raised when the client session initialization handshake or ACK validation fails."""


class PromptError(DeclusorException):
    """Raised when an interactive prompt command or argument is invalid or malformed."""

    def __init__(self, argument: str, /, description: str | None = None) -> None:
        self.argument = argument
        self.description = description

        msg = f"invalid argument: {argument!r}" + (f" ({description})" if description else "")

        super().__init__(msg)


class InvalidOperation(DeclusorException):
    """Raised when an invalid command operation is requested in the current session."""

    def __init__(self, description: str, /) -> None:
        self.description = description
        super().__init__(f"invalid operation: {self.description}")


class CommandError(DeclusorException):
    """Raised when a command fails to prepare, validate, or execute."""

    def __init__(self, description: str, /) -> None:
        self.description = description
        super().__init__(f"command error: {self.description}")


class CommandValidationError(CommandError, InvalidOperation):
    """Raised when command input parameters or DTO invariants are violated."""


class ControllerError(DeclusorException):
    """Raised when an error occurs during controller dispatch, parameter extraction, or execution."""

    def __init__(self, description: str, /) -> None:
        self.description = description
        super().__init__(f"controller error: {self.description}")


class ParserError(DeclusorException):
    """Raised when command-line argument parsing or configuration validation fails."""


class RouterError(DeclusorException):
    """Raised when a route cannot be found or is invalid in the route table."""

    def __init__(self, route: str, /, description: str | None = None) -> None:
        self.route = route
        self.description = description

        msg = f"invalid route: {route!r}" + (f" ({description})" if description else "")

        super().__init__(msg)


class PluginError(DeclusorException):
    """Base exception for plugin discovery, loading, and runtime errors."""


class PluginValidationError(PluginError):
    """Raised when a candidate plugin fails contract validation during discovery or registration."""
