from collections.abc import Generator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from socket import socket
from types import MappingProxyType

from declusor import config, contract, util


@dataclass(frozen=True)
class ShellSocketProfile(contract.IConnectionProfile):
    """Immutable configuration profile for a shell-over-socket client.

    All fields are set at construction time; the dataclass is frozen to prevent
    accidental mutation. This class is pure data — it never performs I/O.
    File loading and script formatting are handled by ``ShellSocketConnection``.
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
    """Size of the buffer to use when reading from the socket. Must be > 0."""

    _supported_functions: Mapping[config.OperationCode, str] = field(
        default_factory=lambda: MappingProxyType(
            {
                config.OperationCode.STORE_FILE: "store_base64_encoded_value",
                config.OperationCode.EXEC_FILE: "execute_base64_encoded_value",
            }
        )
    )
    """Mapping of supported operation codes to their corresponding function names in the client script."""

    def __post_init__(self) -> None:
        object.__setattr__(self, "_supported_functions", MappingProxyType(dict(self._supported_functions)))

        if self._default_buffer_size <= 0:
            raise config.ConnectionFailure("buffer_size must be > 0")

        if self.default_timeout and self.default_timeout < 0:
            raise config.ConnectionFailure("connection_timeout must be >= 0 or None")

    @property
    def default_buffer_size(self) -> int:
        """Default buffer size for socket reads. Must be a positive integer."""

        return self._default_buffer_size

    @property
    def default_timeout(self) -> float | None:
        """Default timeout for socket operations in seconds."""

        return self._default_timeout

    def render_operation_command(self, opcode: "config.OperationCode", /, *args: str) -> str | None:
        """Build the shell command string for a given operation code.

        Looks up the function name that corresponds to *opcode* in
        ``supported_functions`` and appends each argument as a shell-quoted
        token. If no args are provided, returns the bare function name.

        Args:
            opcode: The operation to invoke on the client.
            *args: Positional arguments appended to the function call, each
                shell-quoted via ``shlex.quote``.

        Returns:
            A ready-to-send shell command string, or ``None`` if *opcode*
            is not in ``supported_functions``.
        """

        function_name = self._supported_functions.get(opcode)

        if not function_name:
            return None

        return function_name + (" " + " ".join(util.quote(a) for a in args) if args else "")


class ShellSocketFileStore(contract.IClientFileStore):
    """Filesystem adapter for shell client templates, libraries and payloads."""

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
        """Read and render the shell client bootstrap template."""

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
        """Load and concatenate valid shell libraries."""

        modules: list[bytes] = []

        for file in self._data_paths.library.iterdir():
            if not file.is_file() or not util.validate_file_extension(file, self._library_extensions):
                continue

            try:
                module_content = util.load_file(file)
            except config.InvalidOperation as error:
                raise config.ConnectionFailure(f"Failed to read library file: {file}: {error}") from error

            if module_content:
                modules.append(module_content)

        return b"\n".join(modules)

    def load_module(self, module_name: str, /) -> bytes:
        """Load one operator-selected module from the modules directory.

        Args:
            module_name: Module filename relative to ``data/modules``.

        Returns:
            Raw module contents.

        Raises:
            InvalidOperation: If the module escapes the modules directory, has
                an unsupported extension, or is not a readable file.
        """

        module_path = (self._data_paths.modules / module_name).resolve()

        if not util.validate_file_relative(module_path, self._data_paths.modules):
            raise config.InvalidOperation(f"module path {module_path} is not relative to the module root directory")

        if not util.validate_file_extension(module_path, self._module_extensions):
            raise config.InvalidOperation(f"module has unsupported extension: {module_path}")

        return util.load_file(module_path)


class ShellSocketConnection(contract.IConnection):
    """``IConnection`` implementation over a raw TCP socket.

    Wraps a connected ``socket.socket``, applies ACK-based framing for all
    read/write operations, and manages the library-upload handshake on startup.
    Implements the context manager protocol — the underlying socket is closed
    automatically when the ``with`` block exits.
    """

    def __init__(self, connection: socket, profile: ShellSocketProfile, files: contract.IClientFileStore, /) -> None:
        """Bind a live socket to a profile and prepare the session for use.

        Sets the socket timeout from the profile, then pre-render the client
        script by querying the peer address.

        Args:
            connection: An accepted, connected ``socket.socket`` instance.
            profile: The ``ShellSocketProfile`` providing protocol parameters.
        """

        self._profile = profile
        self._files = files
        self._connection = connection
        self._timeout = profile.default_timeout

        if self._timeout is not None:
            self._connection.settimeout(self._timeout)

    def initialize(self) -> None:
        """Perform the initial protocol handshake.

        Sends the concatenated library scripts to the client, then waits for
        the client's ACK sentinel. Raises ``ConnectionFailure`` if the ACK
        is not received within the configured timeout, or if the value is wrong.

        Raises:
            ConnectionFailure: On timeout or invalid client ACK.
        """

        self.write(self._files.load_library())

        try:
            initial_data = self._connection.recv(self._profile.default_buffer_size)

            if initial_data != self._profile.ack_client_raw:
                raise config.ConnectionFailure("invalid client ACK during session initialization.")
        except (OSError, TimeoutError) as error:
            raise config.ConnectionFailure("failed waiting for client ACK during session initialization.") from error

    @property
    def client(self) -> contract.IConnectionProfile:
        """The ``ShellSocketProfile`` used to configure this connection."""

        return self._profile

    @property
    def timeout(self) -> float | None:
        """Current socket operation timeout in seconds, or ``None`` for no timeout."""

        return self._timeout

    @timeout.setter
    def timeout(self, value: float | None, /) -> None:
        """Update the socket timeout and apply it immediately to the underlying socket.

        Args:
            value: New timeout in seconds, or ``None`` to block indefinitely.
        """

        self._timeout = value
        self._connection.settimeout(value)

    def read(self) -> Generator[bytes, None, None]:
        """Yield the payload of one framed message from the client.

        Reads from the socket in chunks, accumulating data until the client
        ACK sentinel is found. Yields all data preceding the sentinel; the
        sentinel itself is discarded. A rolling tail buffer (size equal to
        ACK length minus one) prevents the sentinel from being split across
        two ``recv`` calls.

        Yields:
            Successive ``bytes`` chunks of the incoming payload.

        Raises:
            ConnectionFailure: On timeout, connection reset, or OS-level I/O error.
        """

        ack, ack_len = self._profile.ack_client_raw, len(self._profile.ack_client_raw)
        buffer = bytearray()

        while True:
            try:
                chunk = self._connection.recv(self._profile.default_buffer_size)

                if not chunk:
                    raise ConnectionResetError("Connection closed by peer")

                combined = buffer + chunk
                ack_index = combined.find(ack)

                if ack_index != -1:
                    if ack_index > 0:
                        yield bytes(combined[:ack_index])

                    break

                if len(combined) >= ack_len:
                    yield_len = len(combined) - (ack_len - 1)

                    yield bytes(combined[:yield_len])

                    buffer = combined[yield_len:]
                else:
                    buffer = combined

            except TimeoutError as e:
                raise config.ConnectionFailure("Timeout while reading from connection") from e
            except (OSError, ConnectionResetError) as e:
                raise config.ConnectionFailure(f"Failed to read from connection: {e}") from e

    def write(self, content: bytes, /) -> None:
        """Send *content* to the client, followed by the server ACK sentinel.

        Both the payload and the sentinel are sent as separate ``sendall``
        calls so every byte is handed to the operating system.

        Args:
            content: The raw bytes payload to transmit.

        Raises:
            ConnectionFailure: On timeout or OS-level I/O error.
        """

        try:
            self._connection.sendall(content)
            self._connection.sendall(self._profile.ack_server_raw)
        except TimeoutError as e:
            raise config.ConnectionFailure("Timeout while writing to connection") from e
        except OSError as e:
            raise config.ConnectionFailure(f"Failed to write to connection: {e}") from e

    def close(self) -> None:
        """Close the underlying socket, releasing the OS file descriptor."""

        self._connection.close()


DEFAULT_SHELL_SOCKET = ShellSocketProfile(
    name="Shell Socket",
    ack_server_raw=b"\x00",
    ack_client_raw=util.hash_sha256(b"\xba\xdc\x00\xff\xee"),
)
"""Default ShellSocketProfile instance with typical configuration for a shell socket client."""
