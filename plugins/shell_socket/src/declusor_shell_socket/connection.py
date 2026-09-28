import secrets
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

    _framing_mode: config.FramingMode = config.FramingMode.EPHEMERAL_ENVELOPE
    """Framing strategy used by this profile."""

    _default_nonce: str | None = None
    """Default or fixed nonce for deterministic testing."""

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
    def default_nonce(self) -> str | None:
        """Default or fixed nonce for deterministic testing."""

        return self._default_nonce

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
        self._current_nonce: str | None = profile.default_nonce

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
    def current_nonce(self) -> str | None:
        """The active ephemeral nonce for the current or most recent command."""

        return self._current_nonce

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

        try:
            for _ in self.read():
                pass
        except (config.ConnectionClosed, config.ConnectionTimeoutError, config.ConnectionError) as error:
            raise config.ConnectionError("Failed waiting for client handshake envelope.") from error

        self._state = contract.ConnectionState.CONNECTED

    def write(self, data: bytes, /, *, nonce: str | None = None) -> None:
        """Send data to the remote client enclosed in an ephemeral transaction envelope."""

        if self._state == contract.ConnectionState.CLOSED:
            raise config.ConnectionClosed("Connection is closed.")

        self._current_nonce = nonce or self._profile.default_nonce or secrets.token_hex(16)
        payload = self._current_nonce.encode("ascii") + b"\x00" + data + b"\x00"

        try:
            self._transport.write(payload)
        except (config.ConnectionClosed, config.ConnectionTimeoutError, config.ConnectionError) as error:
            raise config.ConnectionError(f"Failed to write to connection: {error}") from error

    def read(self) -> Generator[bytes, None, None]:
        """Stream response chunks from the client until the ephemeral envelope delimiter."""

        if self._state == contract.ConnectionState.CLOSED:
            raise config.ConnectionClosed("Connection is closed.")

        if not self._current_nonce:
            raise config.ConnectionError("No active command nonce for read operation.")

        delim = f"__DECLUSOR_EOF_{self._current_nonce}__".encode("ascii")

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
                pos = buffer.find(delim)
                if pos == -1:
                    break

                if pos > 0:
                    yield bytes(buffer[:pos])

                buffer = buffer[pos + len(delim) :]
                if buffer.startswith(b"\n"):
                    buffer = buffer[1:]
                return

            if len(buffer) > len(delim):
                yield bytes(buffer[: -len(delim)])
                buffer = buffer[-len(delim) :]

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
    _framing_mode=config.FramingMode.EPHEMERAL_ENVELOPE,
)
