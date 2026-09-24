from collections.abc import Generator, Mapping
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from socket import socket
from types import MappingProxyType

from declusor import config, contract, util
from declusor.connection.shell_socket import ConnectionState


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
            raise config.ConnectionFailure("buffer_size must be > 0")

        if self.default_timeout and self.default_timeout < 0:
            raise config.ConnectionFailure("connection_timeout must be >= 0 or None")

    @property
    def default_buffer_size(self) -> int:
        """Default buffer size for socket reads."""

        return self._default_buffer_size

    @property
    def default_timeout(self) -> float | None:
        """Default timeout for socket operations in seconds."""

        return self._default_timeout

    def render_operation_command(self, opcode: "config.OperationCode", /, *args: str) -> str | None:
        """Build the Python function call string for a given operation code.

        Produces a Python expression like:
        ``execute_base64_encoded_value('<base64_data>')``
        that will be evaluated by the remote Python agent via ``exec``.

        Args:
            opcode: The operation to invoke on the client.
            *args: Positional arguments appended to the function call,
                each wrapped in single quotes.

        Returns:
            A Python function call string, or ``None`` if *opcode* is not supported.
        """

        function_name = self._supported_functions.get(opcode)

        if not function_name:
            return None

        if args:
            quoted_args = ", ".join(f"'{a}'" for a in args)
            return f"{function_name}({quoted_args})"

        return f"{function_name}()"


class PySocketFileStore(contract.IClientFileStore):
    """Filesystem adapter for Python client templates, libraries and payloads.

    Mirrors ``ShellSocketFileStore`` but loads ``.py`` files for the Python
    client agent. Libraries are concatenated and uploaded during initialization;
    modules are loaded individually on operator request.
    """

    def __init__(
        self,
        client_path: Path,
        data_paths: config.DataPaths,
        library_extensions: tuple[str, ...],
        module_extensions: tuple[str, ...],
        /,
    ) -> None:
        self._client_path = client_path
        self._data_paths = data_paths
        self._library_extensions = library_extensions
        self._module_extensions = module_extensions

    def render_client_script(self, host: str, port: int, acknowledge: bytes, /) -> str:
        """Read and render the Python client bootstrap launcher script.

        Args:
            host: Target host address embedded in the script template.
            port: Target port embedded in the script template.
            acknowledge: Client acknowledgment bytes embedded in the template.

        Returns:
            Rendered Python launcher script ready to execute on the target.

        Raises:
            ConnectionFailure: If the launcher file cannot be read.
        """

        try:
            client_script_template = self._client_path.read_text(encoding="utf-8")
        except OSError as error:
            raise config.ConnectionFailure(f"Failed to read client script: {error}") from error

        return util.format_template(
            client_script_template,
            HOST=host,
            PORT=str(port),
            ACKNOWLEDGE=util.convert_bytes_to_hex(acknowledge),
        )

    def load_library(self) -> bytes:
        """Load and concatenate valid Python helper libraries.

        Returns:
            Concatenated helper contents as bytes, or empty bytes if the helpers
            directory does not exist or contains no valid files.
        """

        # Use namespaced helper path: data/<client>/helpers/
        # Access via the client_path parent's parent / helpers
        # client_path = data/py_socket/launchers/py_socket_client.py
        helpers_dir = self._client_path.parent.parent / "helpers"

        if not helpers_dir.exists():
            return b""

        modules: list[bytes] = []

        for file in sorted(helpers_dir.iterdir()):
            if not file.is_file() or not util.validate_file_extension(file, self._library_extensions):
                continue

            try:
                module_content = util.load_file(file)
            except config.InvalidOperation as error:
                raise config.ConnectionFailure(f"Failed to read helper file: {file}: {error}") from error

            if module_content:
                modules.append(module_content)

        return b"\n\n".join(modules)

    def load_module(self, module_name: str, /) -> bytes:
        """Load one operator-selected module from the modules directory.

        Args:
            module_name: Module filename relative to ``data/<client>/modules/``.

        Returns:
            Raw module contents as bytes.

        Raises:
            InvalidOperation: If the module is outside the modules directory or
                has an unsupported extension.
        """

        modules_dir = self._client_path.parent.parent / "modules"
        module_path = (modules_dir / module_name).resolve()

        if not util.validate_file_relative(module_path, modules_dir):
            raise config.InvalidOperation(f"Module path '{module_name}' is outside the permitted modules directory.")

        if not util.validate_file_extension(module_path, self._module_extensions):
            raise config.InvalidOperation(f"Module '{module_name}' has an unsupported extension. Allowed: {self._module_extensions}")

        return util.load_file(module_path)


class PySocketConnection(contract.IConnection):
    """``IConnection`` implementation for a Python-socket reverse-shell client.

    Shares the connection lifecycle state machine (``ConnectionState``) with
    ``ShellSocketConnection``. Protocol framing and ACK validation are identical;
    the difference lies in the payloads transmitted — Python expressions for
    helper calls and raw shell command strings for system commands.
    """

    def __init__(self, connection: socket, profile: PySocketProfile, files: contract.IClientFileStore, /) -> None:
        """Bind a live socket to a Python-socket profile.

        Args:
            connection: An accepted, connected ``socket.socket`` instance.
            profile: The ``PySocketProfile`` providing protocol parameters.
            files: File store for loading helpers and modules.
        """

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
        """Set the socket timeout in seconds."""

        self._timeout = value
        self._connection.settimeout(value)

    def initialize(self) -> None:
        """Perform the Python agent initialization handshake.

        Transmits the concatenated helper libraries to the client for evaluation,
        then waits for the expected ACK sentinel.

        Raises:
            ConnectionFailure: On timeout, invalid ACK, or closed connection.
        """

        if self._state == ConnectionState.CLOSED:
            raise config.ConnectionFailure("Cannot initialize a closed connection.")

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
                    raise config.ConnectionFailure("Connection closed by client before receiving ACK.")

                received_ack.extend(chunk)

            if bytes(received_ack) != expected_ack:
                raise config.ConnectionFailure("Invalid client ACK during session initialization.")
        except (OSError, TimeoutError) as error:
            raise config.ConnectionFailure("Failed waiting for client ACK during session initialization.") from error

        self._state = ConnectionState.CONNECTED

    def write(self, data: bytes, /) -> None:
        """Send a null-delimited payload to the remote Python agent.

        Args:
            data: Payload bytes to transmit.

        Raises:
            ConnectionClosed: If the connection is not in OPEN state.
            ConnectionWriteError: If the socket transmission fails.
        """
        if self._state == ConnectionState.CLOSED:
            raise config.ConnectionClosed("Connection is closed.")

        try:
            self._connection.sendall(data + b"\x00")
            self._connection.recv(len(self._profile.ack_server_raw))
        except (OSError, TimeoutError) as error:
            raise config.ConnectionWriteError(f"Failed to write to connection: {error}") from error

    def read(self) -> Generator[bytes, None, None]:
        """Stream response chunks from the Python agent until the ACK sentinel.

        Yields:
            Successive byte chunks from the agent's response.

        Raises:
            ConnectionClosed: If the connection terminates unexpectedly.
        """
        ack = self._profile.ack_client_raw
        buffer = bytearray()

        while True:
            try:
                chunk = self._connection.recv(self._profile.default_buffer_size)
            except (OSError, TimeoutError) as error:
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
"""Default PySocketProfile with standard Declusor protocol parameters."""
