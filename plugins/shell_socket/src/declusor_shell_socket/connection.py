from collections.abc import Generator, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from declusor import config, contract, util


@dataclass(frozen=True)
class ShellSocketProfile(contract.IConnectionProfile):
    """Immutable configuration profile for a shell-over-socket client.

    All fields are set at construction time; the dataclass is frozen to prevent
    accidental mutation. This class is pure data — it never performs I/O.
    """

    name: str
    """Name of the profile, used for display purposes."""

    ack_server_raw: bytes
    """Acknowledgment byte sequence sent by the server."""

    ack_client_raw: bytes
    """Acknowledgment byte sequence sent by the client."""

    _default_timeout: float | None = 1.0
    """Timeout in seconds for socket operations. Set to None for no timeout."""

    _framing_mode: config.FramingMode = config.FramingMode.SENTINEL
    """Framing strategy used by this profile."""

    _default_buffer_size: int = 2**8
    """Size of the buffer to use when reading from the socket. Must be > 0."""

    _supported_functions: Mapping[config.OperationCode, str] = field(
        default_factory=lambda: MappingProxyType(
            {
                config.OperationCode.STORE_FILE: "store_base64_encoded_value",
                config.OperationCode.EXEC_FILE: "execute_base64_encoded_value",
            }
        )
    )
    """Mapping of supported operation codes to their corresponding function names."""

    def __post_init__(self) -> None:
        object.__setattr__(self, "_supported_functions", MappingProxyType(dict(self._supported_functions)))

        if self._default_buffer_size <= 0:
            raise config.ConnectionError("buffer_size must be > 0")

        if self.default_timeout and self.default_timeout < 0:
            raise config.ConnectionError("connection_timeout must be >= 0 or None")

    @property
    def framing_mode(self) -> config.FramingMode:
        """Framing strategy used by this profile."""

        return self._framing_mode

    @property
    def default_buffer_size(self) -> int:
        """Default buffer size for socket reads."""

        return self._default_buffer_size

    @property
    def default_timeout(self) -> float | None:
        """Default timeout for socket operations in seconds."""

        return self._default_timeout

    def render_operation_command(self, opcode: "config.OperationCode", /, *args: str) -> str | None:
        """Build the shell command string for a given operation code.

        Args:
            opcode: The operation to invoke on the client.
            *args: Positional arguments appended to the function call.

        Returns:
            A ready-to-send shell command string, or ``None`` if unsupported.
        """

        function_name = self._supported_functions.get(opcode)

        if not function_name:
            return None

        return function_name + (" " + " ".join(util.quote(a) for a in args) if args else "")


class ShellSocketConnection(contract.IConnection):
    """``IConnection`` implementation for a Bash-over-TCP reverse-shell client."""

    def __init__(
        self,
        transport: contract.ITransport,
        profile: ShellSocketProfile,
        files: contract.IPluginProcessor,
        /,
    ) -> None:
        self._profile = profile
        self._files = files
        self._transport = transport
        self._state = contract.ConnectionState.CREATED

        if profile.default_timeout is not None:
            self._transport.timeout = profile.default_timeout

    @property
    def state(self) -> contract.ConnectionState:
        """Current lifecycle state of the connection."""

        return self._state

    @property
    def profile(self) -> ShellSocketProfile:
        """The connection profile."""

        return self._profile

    @property
    def timeout(self) -> float | None:
        """Current transport timeout in seconds."""

        return self._transport.timeout

    @timeout.setter
    def timeout(self, value: float | None) -> None:
        self._transport.timeout = value

    def handshake(self) -> None:
        """Perform the client initialization handshake."""

        if self._state == contract.ConnectionState.CLOSED:
            raise config.ConnectionError("Cannot initialize a closed connection.")

        self._state = contract.ConnectionState.INITIALIZING
        self.write(self._files.helpers)

        expected_ack = self._profile.ack_client_raw
        try:
            received_ack = self._transport.read_exact(len(expected_ack))
            if received_ack != expected_ack:
                raise config.ConnectionError("Invalid client ACK during session initialization.")
        except (config.ConnectionClosed, config.ConnectionTimeoutError, config.ConnectionError) as error:
            raise config.ConnectionError("Failed waiting for client ACK during session initialization.") from error

        self._state = contract.ConnectionState.CONNECTED

    def write(self, data: bytes, /) -> None:
        """Send data to the remote client."""

        if self._state == contract.ConnectionState.CLOSED:
            raise config.ConnectionClosed("Connection is closed.")

        try:
            self._transport.write(data)
            self._transport.write(self._profile.ack_server_raw)
        except (config.ConnectionClosed, config.ConnectionTimeoutError, config.ConnectionError) as error:
            raise config.ConnectionError(f"Failed to write to connection: {error}") from error

    def read(self) -> Generator[bytes, None, None]:
        """Stream response chunks from the client until the ACK sentinel."""

        ack = self._profile.ack_client_raw
        buffer = bytearray()

        while True:
            try:
                chunk = self._transport.read(self._profile.default_buffer_size)
            except (config.ConnectionClosed, config.ConnectionTimeoutError, config.ConnectionError) as error:
                raise config.ConnectionClosed(f"Connection interrupted during read: {error}") from error

            if not chunk:
                raise config.ConnectionClosed("Connection closed by client during response stream.")

            buffer.extend(chunk)

            while True:
                ack_pos = buffer.find(ack)
                if ack_pos == -1:
                    break

                if ack_pos > 0:
                    yield bytes(buffer[:ack_pos])

                buffer = buffer[ack_pos + len(ack) :]
                return

            if len(buffer) > len(ack):
                yield bytes(buffer[: -len(ack)])
                buffer = buffer[-len(ack) :]

    def __enter__(self) -> "ShellSocketConnection":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying transport idempotently."""

        if self._state == contract.ConnectionState.CLOSED:
            return

        self._state = contract.ConnectionState.CLOSED
        self._transport.close()


DEFAULT_SHELL_SOCKET = ShellSocketProfile(
    name="Shell Socket",
    ack_server_raw=config.Settings.DEFAULT_SERVER_ACK,
    ack_client_raw=util.hash_sha256(config.Settings.DEFAULT_CLIENT_ACK_SEED),
)
