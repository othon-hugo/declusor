from enum import IntEnum, StrEnum


class ExecutionMode(StrEnum):
    """Enumeration of application execution modes."""

    CLI = "cli"
    API = "api"
    MCP = "mcp"
    HTTP = "http"

    @classmethod
    def default(cls) -> "ExecutionMode":
        """Return the default execution mode (CLI)."""

        return cls.CLI

    @classmethod
    def from_string(cls, value: str) -> "ExecutionMode":
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
    """Enumeration of file operation codes."""

    EXEC_FILE = "EXECUTE_FILE"
    STORE_FILE = "STORE_FILE"


class FramingMode(StrEnum):
    """Enumeration of transport stream framing strategies."""

    SENTINEL = "sentinel"
    CHUNKED_TLV = "chunked_tlv"
    EPHEMERAL_ENVELOPE = "ephemeral_envelope"


class ChannelType(IntEnum):
    """Enumeration of multiplexed stream channel identifiers."""

    PROCESS_EXIT = 0
    STDOUT = 1
    STDERR = 2
    SIGNAL = 3
    HEARTBEAT = 4
