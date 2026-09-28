import struct
from collections.abc import Generator, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from declusor import config, contract, util


@dataclass(frozen=True)
class PySocketProfile(contract.IConnectionProfile):
    """Immutable configuration profile for a Python-socket reverse-shell client.

    Configures the operation templates and protocol parameters for a Python
    agent that evaluates payloads natively in its own runtime (via ``exec``) or
    through the OS shell (via ``subprocess``). This profile is pure data — it
    never performs I/O.
    """

    name: str
    """Name of the profile, used for display purposes."""

    ack_server_raw: bytes
    """Acknowledgment byte sequence sent by the server."""

    ack_client_raw: bytes
    """Acknowledgment byte sequence sent by the client."""

    _default_timeout: float | None = 1.0
    """Timeout in seconds for socket operations. Set to None for no timeout."""

    _framing_mode: config.FramingMode = config.FramingMode.CHUNKED_TLV
    """Framing strategy used by this profile."""

    _default_buffer_size: int = 2**8
    """Size of the read buffer. Must be > 0."""

    _supported_functions: Mapping[config.OperationCode, str] = field(
        default_factory=lambda: MappingProxyType(
            {
                config.OperationCode.STORE_FILE: "store_base64_encoded_value",
                config.OperationCode.EXEC_FILE: "execute_base64_encoded_value",
            }
        )
    )
    """Mapping of operation codes to Python helper function names."""

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
        """Build the Python function call string for a given operation code."""

        function_name = self._supported_functions.get(opcode)

        if not function_name:
            return None

        if args:
            quoted_args = ", ".join(repr(a) for a in args)
            return f"{function_name}({quoted_args})"

        return f"{function_name}()"


class PySocketConnection(contract.IConnection):
    """``IConnection`` implementation for a Python-socket reverse-shell client."""

    def __init__(
        self,
        transport: contract.ITransport,
        profile: PySocketProfile,
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
    def profile(self) -> PySocketProfile:
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
        """Perform the Python agent initialization handshake."""

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
        """Send a TLV-framed payload to the remote Python agent."""

        if self._state == contract.ConnectionState.CLOSED:
            raise config.ConnectionClosed("Connection is closed.")

        frame = struct.pack(">BI", config.ChannelType.STDOUT, len(data)) + data

        try:
            self._transport.write(frame)
        except (config.ConnectionClosed, config.ConnectionTimeoutError, config.ConnectionError) as error:
            raise config.ConnectionError(f"Failed to write to connection: {error}") from error

    def read(self) -> Generator[bytes, None, None]:
        """Stream response chunks from the Python agent until a PROCESS_EXIT frame."""

        if self._state == contract.ConnectionState.CLOSED:
            raise config.ConnectionClosed("Connection is closed.")

        while True:
            try:
                header = self._transport.read_exact(5)
            except config.ConnectionTimeoutError:
                raise
            except (config.ConnectionClosed, config.ConnectionError) as error:
                raise config.ConnectionClosed(f"Connection interrupted during read: {error}") from error

            channel, length = struct.unpack(">BI", header)

            if channel == config.ChannelType.PROCESS_EXIT:
                if length > 0:
                    try:
                        self._transport.read_exact(length)
                    except config.ConnectionTimeoutError:
                        raise
                    except (config.ConnectionClosed, config.ConnectionError) as error:
                        raise config.ConnectionClosed(f"Connection interrupted reading exit frame: {error}") from error

                return

            if length == 0:
                continue

            try:
                payload = self._transport.read_exact(length)
            except config.ConnectionTimeoutError:
                raise
            except (config.ConnectionClosed, config.ConnectionError) as error:
                raise config.ConnectionClosed(f"Connection interrupted reading payload: {error}") from error

            if channel in (config.ChannelType.STDOUT, config.ChannelType.STDERR):
                yield payload

    def __enter__(self) -> "PySocketConnection":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying transport idempotently."""

        if self._state == contract.ConnectionState.CLOSED:
            return

        self._state = contract.ConnectionState.CLOSED
        self._transport.close()


DEFAULT_PY_SOCKET = PySocketProfile(
    name="Python Socket",
    ack_server_raw=config.Settings.DEFAULT_SERVER_ACK,
    ack_client_raw=util.hash_sha256(config.Settings.DEFAULT_CLIENT_ACK_SEED),
)
