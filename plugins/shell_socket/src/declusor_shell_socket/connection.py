from collections.abc import Callable, Generator
from typing import Final

from declusor import config, contract, util


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
        timeout: float | None = config.DEFAULT_CONNECTION_TIMEOUT,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
        fixed_nonce: str | None = None,
        nonce_factory: Callable[[], str] = util.generate_nonce,
    ) -> None:
        if buffer_size <= 0:
            raise config.ConnectionError("buffer_size must be > 0")

        self._transport = transport
        self._transport.timeout = timeout

        self._renderer = renderer
        self._files = files
        self._buffer_size = buffer_size
        self._fixed_nonce = fixed_nonce
        self._nonce_factory = nonce_factory
        self._current_nonce = fixed_nonce

        self._state = contract.ConnectionState.CREATED
        self._read_buffer = bytearray()

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
        if not self._current_nonce:
            raise config.ConnectionError("No active command nonce.")

        return f"__DECLUSOR_EOF_{self._current_nonce}__".encode("ascii")

    def handshake(self) -> None:
        """Perform the client initialization handshake."""

        self.ensure_can_handshake()

        self._state = contract.ConnectionState.INITIALIZING

        helpers_payload = b"\n".join(self._files.load_all_helpers().values())
        self.write(helpers_payload)

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

        delim = self.delim
        delim_len = len(delim)

        if not delim:
            raise ValueError("Delimiter cannot be empty.")

        buffer = self._read_buffer

        while True:
            pos = buffer.find(delim)

            if pos != -1:
                if pos > 0:
                    yield bytes(buffer[:pos])

                del buffer[: pos + delim_len]

                if buffer.startswith(b"\r\n"):
                    del buffer[:2]
                elif buffer.startswith(b"\n"):
                    del buffer[:1]

                self._current_nonce = None
                return

            keep_len = delim_len - 1

            if len(buffer) > keep_len:
                safe_cutoff = len(buffer) - keep_len

                yield bytes(buffer[:safe_cutoff])
                del buffer[:safe_cutoff]

            try:
                chunk = self._transport.read(self._buffer_size)
            except (config.ConnectionClosed, config.ConnectionTimeoutError, config.ConnectionError) as error:
                if isinstance(error, config.ConnectionClosed):
                    raise

                raise config.ConnectionClosed(f"Connection interrupted during read: {error}") from error

            if not chunk:
                raise config.ConnectionClosed("Connection closed by client during response stream.")

            buffer.extend(chunk)

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
