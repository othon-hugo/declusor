from collections.abc import Generator, Mapping
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from socket import socket
from types import MappingProxyType

from declusor import config, contract, util
from declusor.contract import ConnectionState


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
            raise contract.ConnectionError("buffer_size must be > 0")

        if self.default_timeout and self.default_timeout < 0:
            raise contract.ConnectionError("connection_timeout must be >= 0 or None")

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
            quoted_args = ", ".join(f"'{a}'" for a in args)
            return f"{function_name}({quoted_args})"

        return f"{function_name}()"


class PySocketFileStore(contract.IClientFileStore):
    """Filesystem adapter for Python client templates, libraries and payloads.

    Resolves launchers, helpers and modules from the plugin's own self-contained
    assets directory, with support for user-specified overlay directories.
    """

    def __init__(
        self,
        launcher_path: Path,
        helpers_dir: Path,
        modules_dir: Path,
        library_extensions: tuple[str, ...] = (".py",),
        module_extensions: tuple[str, ...] = (".py",),
    ) -> None:
        self._launcher_path = launcher_path
        self._helpers_dir = helpers_dir
        self._modules_dir = modules_dir
        self._library_extensions = library_extensions
        self._module_extensions = module_extensions

    def render_client_script(self, host: str, port: int, acknowledge: bytes, /) -> str:
        """Read and render the Python client bootstrap launcher script."""
        try:
            client_script_template = self._launcher_path.read_text(encoding="utf-8")
        except OSError as error:
            raise contract.ConnectionError(f"Failed to read client script: {error}") from error

        return util.format_template(
            client_script_template,
            HOST=host,
            PORT=str(port),
            ACKNOWLEDGE=util.convert_bytes_to_hex(acknowledge),
        )

    def load_library(self) -> bytes:
        """Load and concatenate valid Python helper libraries."""
        if not self._helpers_dir.exists():
            return b""

        modules: list[bytes] = []

        for file in sorted(self._helpers_dir.iterdir()):
            if not file.is_file() or not util.validate_file_extension(file, self._library_extensions):
                continue

            try:
                module_content = util.load_file(file)
            except config.InvalidOperation as error:
                raise contract.ConnectionError(f"Failed to read helper file: {file}: {error}") from error

            if module_content:
                modules.append(module_content)

        return b"\n\n".join(modules)

    def load_module(self, module_name: str, /) -> bytes:
        """Load one operator-selected module from the modules directory."""
        module_path = (self._modules_dir / module_name).resolve()

        if not util.validate_file_relative(module_path, self._modules_dir):
            raise config.InvalidOperation(f"Module path '{module_name}' is outside the permitted modules directory.")

        if not util.validate_file_extension(module_path, self._module_extensions):
            raise config.InvalidOperation(f"Module '{module_name}' has an unsupported extension. Allowed: {self._module_extensions}")

        return util.load_file(module_path)


class PySocketConnection(contract.IConnection):
    """``IConnection`` implementation for a Python-socket reverse-shell client."""

    def __init__(self, connection: socket, profile: PySocketProfile, files: contract.IClientFileStore, /) -> None:
        self._profile = profile
        self._files = files
        self._connection = connection
        self._timeout = profile.default_timeout
        self._state = ConnectionState.CREATED

        if self._timeout is not None:
            self._connection.settimeout(self._timeout)

    @property
    def state(self) -> ConnectionState:
        """Current lifecycle state of the connection."""
        return self._state

    @property
    def client(self) -> PySocketProfile:
        """The connection profile."""
        return self._profile

    @property
    def timeout(self) -> float | None:
        """Current socket timeout in seconds."""
        return self._timeout

    @timeout.setter
    def timeout(self, value: float | None) -> None:
        self._timeout = value
        self._connection.settimeout(value)

    def initialize(self) -> None:
        """Perform the Python agent initialization handshake."""
        if self._state == ConnectionState.CLOSED:
            raise contract.ConnectionError("Cannot initialize a closed connection.")

        self._state = ConnectionState.INITIALIZING
        self.write(self._files.load_library())

        expected_ack = self._profile.ack_client_raw
        ack_len = len(expected_ack)
        received_ack = bytearray()

        try:
            while len(received_ack) < ack_len:
                remaining = ack_len - len(received_ack)
                read_size = min(self._profile.default_buffer_size, remaining)
                chunk = self._connection.recv(read_size)

                if not chunk:
                    raise contract.ConnectionError("Connection closed by client before receiving ACK.")

                received_ack.extend(chunk)

            if bytes(received_ack) != expected_ack:
                raise contract.ConnectionError("Invalid client ACK during session initialization.")
        except (OSError, TimeoutError) as error:
            raise contract.ConnectionError("Failed waiting for client ACK during session initialization.") from error

        self._state = ConnectionState.CONNECTED

    def write(self, data: bytes, /) -> None:
        """Send a null-delimited payload to the remote Python agent."""
        if self._state == ConnectionState.CLOSED:
            raise contract.ConnectionClosed("Connection is closed.")

        try:
            self._connection.sendall(data + b"\x00")
            self._connection.recv(len(self._profile.ack_server_raw))
        except (OSError, TimeoutError) as error:
            raise contract.ConnectionError(f"Failed to write to connection: {error}") from error

    def read(self) -> Generator[bytes, None, None]:
        """Stream response chunks from the Python agent until the ACK sentinel."""
        ack = self._profile.ack_client_raw
        buffer = bytearray()

        while True:
            try:
                chunk = self._connection.recv(self._profile.default_buffer_size)
            except (OSError, TimeoutError) as error:
                raise contract.ConnectionClosed(f"Connection interrupted during read: {error}") from error

            if not chunk:
                raise contract.ConnectionClosed("Connection closed by client during response stream.")

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

    def __enter__(self) -> "PySocketConnection":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying socket idempotently."""
        if self._state == ConnectionState.CLOSED:
            return

        self._state = ConnectionState.CLOSED

        with suppress(OSError):
            self._connection.close()


DEFAULT_PY_SOCKET = PySocketProfile(
    name="Python Socket",
    ack_server_raw=config.Settings.DEFAULT_SERVER_ACK,
    ack_client_raw=util.hash_sha256(config.Settings.DEFAULT_CLIENT_ACK_SEED),
)
