from enum import IntEnum, StrEnum


class DeclusorPlugins(StrEnum):
    SHELL_SOCKET = "shell_socket"
    """POSIX shell socket client transport plugin."""

    PY_SOCKET = "py_socket"
    """Cross-platform Python socket client transport plugin."""


class LauncherOutputMode(StrEnum):
    """Enumeration of output delivery modes for the generated client launcher."""

    TERMINAL = "terminal"
    """Write launcher to the operator view (default behaviour)."""

    SILENT = "silent"
    """Suppress all launcher output."""

    FILE = "file"
    """Write launcher to a file path declared in LauncherDelivery.output_path."""


class LauncherKind(StrEnum):
    """Enumeration of client launcher delivery forms."""

    STAGED = "staged"
    """Deliver a lightweight Stage-0 loader that pulls the client over the socket."""

    STAGELESS = "stageless"
    """Deliver a complete monolithic self-contained client launcher."""

    @classmethod
    def from_string(cls, value: str, /) -> "LauncherKind":
        """Parse launcher kind from string in a case-insensitive manner.

        Args:
            value: Kind name (e.g. 'staged', 'stageless').

        Returns:
            Matching LauncherKind member.

        Raises:
            ValueError: If the string does not match any valid launcher kind.
        """

        normalized = value.strip().lower()

        for member in cls:
            if member.value == normalized:
                return member

        choices = ", ".join(repr(m.value) for m in cls)

        raise ValueError(f"Invalid launcher kind: {value!r}. Valid choices: {choices}")


class ExecutionMode(StrEnum):
    """Enumeration of application execution modes."""

    CLI = "cli"
    """Interactive terminal REPL and prompt loop execution mode."""

    API = "api"
    """Programmatic API daemon mode for external service integration."""

    MCP = "mcp"
    """Model Context Protocol server mode for agentic tool calling."""

    HTTP = "http"
    """HTTP RESTful server mode for web-based remote interactions."""

    @classmethod
    def from_string(cls, value: str, /) -> "ExecutionMode":
        """Parse execution mode from string in a case-insensitive manner.

        Args:
            value: Mode name (e.g. 'cli', 'api', 'mcp', 'http').

        Returns:
            Matching ExecutionMode member.

        Raises:
            ValueError: If the string does not match any valid execution mode.
        """

        normalized = value.strip().lower()

        for mode in cls:
            if mode.value == normalized:
                return mode

        valid_modes = ", ".join(repr(m.value) for m in cls)

        raise ValueError(f"Invalid execution mode: {value!r}. Choose from: {valid_modes}")


class ExitCode(IntEnum):
    """Process exit codes for CLI execution."""

    SUCCESS = 0
    """Normal successful execution."""

    FAILURE = 1
    """Runtime error or application exception."""

    USAGE_ERROR = 2
    """Command-line parsing or invocation argument error."""


class CoreRoute(StrEnum):
    """Reserved framework command routes."""

    HELP = "help"
    """Display general or command-specific usage documentation."""

    EXIT = "exit"
    """Terminate the active session and exit the application."""


class OfficialRoute(StrEnum):
    """Standard operation command routes provided by framework controllers."""

    LOAD = "load"
    """Load a remote agent module from assets."""

    COMMAND = "command"
    """Execute a system shell command."""

    EVAL = "eval"
    """Evaluate code in the remote agent runtime."""

    SHELL = "shell"
    """Start an interactive bidirectional remote shell."""

    UPLOAD = "upload"
    """Upload a local file to the remote agent."""

    EXECUTE = "execute"
    """Transmit and execute a local script remotely."""


class RouteCompletionMode(StrEnum):
    """Autocompletion target semantics for command arguments."""

    NONE = "none"
    """Command does not accept path-based autocompletion."""

    HOST_PATH = "host_path"
    """Complete file and directory paths on the local operator host filesystem."""

    MODULE_PATH = "module_path"
    """Complete module paths within the active plugin assets/modules directory."""

    ASSET_PATH = "asset_path"
    """Complete asset file paths within the active plugin assets directory."""


class TransportLayer(StrEnum):
    """Recognized composable transport layer decorators."""

    XOR = "xor"
    """Symmetric XOR obfuscation transport stream cipher layer."""


class OperationCode(StrEnum):
    """Enumeration of client operation codes."""

    EXEC_COMMAND = "EXECUTE_COMMAND"
    """Execute a raw shell command string via the client's operating system environment."""

    EXEC_CODE = "EXECUTE_CODE"
    """Evaluate native code directly in the target client's in-memory runtime scope."""

    EXEC_FILE = "EXECUTE_FILE"
    """Encode and transmit a local script file to be executed on the remote client."""

    STORE_FILE = "STORE_FILE"
    """Encode and store a local file onto the remote client's filesystem without execution."""

    LOAD_MODULE = "LOAD_MODULE"
    """Load an on-demand payload module into the active client's memory or runtime environment."""


class FramingMode(StrEnum):
    """Enumeration of transport stream framing strategies."""

    SENTINEL = "sentinel"
    """Delimits frames using fixed sentinel byte sequences (e.g. newline or magic marker)."""

    CHUNKED_TLV = "chunked_tlv"
    """Binary Type-Length-Value chunk framing with explicit channel and length headers."""

    EPHEMERAL_ENVELOPE = "ephemeral_envelope"
    """Wraps frames in dynamically generated per-command boundary envelopes."""


class ChannelType(IntEnum):
    """Enumeration of multiplexed stream transport buses (barramentos)."""

    PROCESS_EXIT = 0
    """Terminal signaling frame indicating remote command execution completion."""

    STDOUT = 1
    """Standard output stream bus from remote process execution."""

    STDERR = 2
    """Standard error stream bus from remote process execution."""

    STDIN = 3
    """Standard input and command transmission bus from server to client."""

    SIGNAL = 4
    """Out-of-band operational signals and control messages (e.g. SIGINT, stop)."""

    HEARTBEAT = 5
    """Periodic liveness probe frames verifying connection health."""
