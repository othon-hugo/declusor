from collections.abc import Callable, Generator, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

from declusor import config, contract, util

DEFAULT_CONNECTION_TIMEOUT: Final[float | None] = 1.0


@dataclass(frozen=True)
class ShellSocketRenderer(contract.IOperationRenderer):
    """Translates OperationCode values to Bash shell command strings.

    Maps abstract operation codes to concrete Bash helper function invocations
    executed by the client process. This renderer is pure data — it never
    performs I/O.
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
    """Mapping of supported operation codes to their corresponding function names."""

    def __post_init__(self) -> None:
        object.__setattr__(self, "_supported_functions", MappingProxyType(dict(self._supported_functions)))

    @property
    def supported_functions(self) -> Mapping[config.OperationCode, str]:
        """Mapping of supported operation codes to their corresponding function names."""

        return self._supported_functions

    def render_operation_command(self, opcode: "config.OperationCode", /, *args: str) -> str | None:
        """Build the shell command string for a given operation code.

        Args:
            opcode: The operation to invoke on the client.
            *args: Positional arguments appended to the function call.

        Returns:
            A ready-to-send shell command string, or ``None`` if unsupported.
        """

        if opcode in (config.OperationCode.EXEC_COMMAND, config.OperationCode.EXEC_CODE):
            return args[0] if args else ""

        function_name = self._supported_functions.get(opcode)

        if not function_name:
            return None

        return function_name + (" " + " ".join(util.quote(a) for a in args) if args else "")


ShellSocketProfile = ShellSocketRenderer


class ShellSocketConnection(contract.IConnection):
    """``IConnection`` implementation for a Bash-over-TCP reverse-shell client."""

    DEFAULT_BUFFER_SIZE: Final[int] = 2**8
    """Size of the buffer to use when reading from the socket. Must be > 0."""

    def __init__(
        self,
        transport: contract.ITransport,
        renderer: contract.IOperationRenderer,
        files: contract.IPluginProcessor,
        /,
        *,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        fixed_nonce: str | None = None,
        nonce_factory: Callable[[], str] = util.generate_nonce,
        timeout: float | None = DEFAULT_CONNECTION_TIMEOUT,
    ) -> None:
        if buffer_size <= 0:
            raise config.ConnectionError("buffer_size must be > 0")

        self._transport = transport
        self._renderer = renderer
        self._files = files
        self._buffer_size = buffer_size
        self._fixed_nonce = fixed_nonce
        self._nonce_factory = nonce_factory
        self._state = contract.ConnectionState.CREATED
        self._current_nonce: str | None = fixed_nonce

        if timeout is not None:
            self._transport.timeout = timeout

    @property
    def state(self) -> contract.ConnectionState:
        """Current lifecycle state of the connection."""

        return self._state

    @property
    def renderer(self) -> contract.IOperationRenderer:
        """The connection operation renderer."""

        return self._renderer

    @property
    def profile(self) -> contract.IOperationRenderer:
        """Deprecated backward-compatible alias for :attr:`renderer`."""

        return self._renderer

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
            raise config.ConnectionHandshakeError("Failed waiting for client handshake envelope.") from error

        self._state = contract.ConnectionState.CONNECTED

    def write(self, data: bytes, /, *, nonce: str | None = None) -> None:
        """Send data to the remote client enclosed in an ephemeral transaction envelope."""

        if self._state == contract.ConnectionState.CLOSED:
            raise config.ConnectionClosed("Connection is closed.")

        self._current_nonce = nonce or self._fixed_nonce or self._nonce_factory()
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
                chunk = self._transport.read(self._buffer_size)
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


DEFAULT_SHELL_SOCKET = ShellSocketRenderer()
