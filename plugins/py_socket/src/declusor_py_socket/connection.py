import struct
from collections.abc import Generator, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

from declusor import config, contract, util

DEFAULT_CONNECTION_TIMEOUT: Final[float | None] = 1.0


@dataclass(frozen=True)
class PySocketRenderer(contract.IOperationRenderer):
    """Translates OperationCode values to Python function call syntax.

    Maps abstract operation codes to concrete Python helper invocations for an
    agent that evaluates payloads natively in its own runtime (via ``exec``) or
    through the OS shell (via ``subprocess``). This renderer is pure data — it
    never performs I/O.
    """

    _supported_functions: Final[Mapping[config.OperationCode, str]] = field(
        default_factory=lambda: MappingProxyType(
            {
                config.OperationCode.STORE_FILE: "store_base64_encoded_value",
                config.OperationCode.EXEC_FILE: "execute_base64_encoded_value",
                config.OperationCode.LOAD_MODULE: "execute_base64_encoded_value",
            }
        )
    )
    """Mapping of operation codes to Python helper function names."""

    def __post_init__(self) -> None:
        object.__setattr__(self, "_supported_functions", MappingProxyType(dict(self._supported_functions)))

    @property
    def supported_functions(self) -> Mapping[config.OperationCode, str]:
        """Mapping of supported operation codes to Python helper function names."""

        return self._supported_functions

    def render_operation_command(self, opcode: "config.OperationCode", /, *args: str) -> str | None:
        """Build the Python function call string for a given operation code."""

        if opcode == config.OperationCode.EXEC_COMMAND:
            command = args[0] if args else ""
            return f"execute_system_command({command!r})"

        if opcode == config.OperationCode.EXEC_CODE:
            return args[0] if args else ""

        function_name = self._supported_functions.get(opcode)

        if not function_name:
            return None

        if args:
            quoted_args = ", ".join(repr(a) for a in args)
            return f"{function_name}({quoted_args})"

        return f"{function_name}()"


PySocketProfile = PySocketRenderer


class PySocketConnection(contract.IConnection):
    """``IConnection`` implementation for a Python-socket reverse-shell client."""

    def __init__(
        self,
        transport: contract.ITransport,
        renderer: contract.IOperationRenderer,
        files: contract.IPluginProcessor,
        /,
        *,
        expected_ack: bytes = util.hash_sha256(config.DEFAULT_CLIENT_ACK_SEED),
        timeout: float | None = DEFAULT_CONNECTION_TIMEOUT,
    ) -> None:
        self._renderer = renderer
        self._files = files
        self._transport = transport
        self._expected_ack = expected_ack
        self._state = contract.ConnectionState.CREATED

        if timeout is not None:
            self._transport.timeout = timeout

    @property
    def state(self) -> contract.ConnectionState:
        """Current lifecycle state of the connection."""

        return self._state

    @property
    def renderer(self) -> contract.IOperationRenderer:
        """The command syntax renderer."""

        return self._renderer

    @property
    def profile(self) -> contract.IOperationRenderer:
        """Backward-compatible alias for renderer."""

        return self._renderer

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

        expected_ack = self._expected_ack
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


DEFAULT_PY_SOCKET = PySocketRenderer()
