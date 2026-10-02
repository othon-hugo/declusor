from enum import IntEnum, StrEnum


class DeclusorPlugins(StrEnum):
    SHELL_SOCKET = "shell_socket"
    """POSIX shell socket client transport plugin."""

    PY_SOCKET = "py_socket"
    """Cross-platform Python socket client transport plugin."""


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

        raise ValueError(f"Invalid execution mode: '{value}'. Choose from: {valid_modes}")


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
    """Enumeration of multiplexed stream channel identifiers."""

    PROCESS_EXIT = 0
    """Terminal signaling frame indicating remote command execution completion."""

    STDOUT = 1
    """Standard output stream data from remote command or process execution."""

    STDERR = 2
    """Standard error stream data from remote command or process execution."""

    SIGNAL = 3
    """Out-of-band operational signals and control messages (e.g. SIGINT, stop)."""

    HEARTBEAT = 4
    """Periodic liveness probe frames verifying connection health."""
