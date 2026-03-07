from dataclasses import dataclass, field
from pathlib import Path
from socket import socket
from typing import Generator

from declusor import config, interface, util


@dataclass(frozen=True)
class ShellSocketProfile(interface.IProfile):
    """Immutable configuration profile for a shell-over-socket client.

    All fields are set at construction time; the dataclass is frozen to prevent
    accidental mutation. This class is pure data — it never performs I/O.
    File loading and script formatting are handled by ``ShellSocketConnection``.
    """

    name: str
    """Name of the profile, used for display purposes."""

    client_path: Path
    """Path to the client script template. This script will be formatted with connection details."""

    ack_server_raw: bytes
    """Acknowledgment byte sequence sent by the server."""

    ack_client_raw: bytes
    """Acknowledgment byte sequence sent by the client."""

    allowed_payload_extensions: tuple[str, ...]
    """Allowed file extensions for payload scripts."""

    allowed_library_extensions: tuple[str, ...]
    """Allowed file extensions for library scripts."""

    connection_timeout: float | None = 1.0
    """Timeout in seconds for socket operations. Set to None for no timeout."""

    buffer_size: int = 2**8
    """Size of the buffer to use when reading from the socket. Must be > 0."""

    supported_functions: dict[config.OperationCode, str] = field(
        default_factory=lambda: {
            config.OperationCode.STORE_FILE: "store_base64_encoded_value",
            config.OperationCode.EXEC_FILE: "execute_base64_encoded_value",
        }
    )
    """Mapping of supported operation codes to their corresponding function names in the client script."""

    library_root_directory: Path = config.BasePath.LIBRARY_DIR
    """Root directory for library scripts."""

    payload_root_directory: Path = config.BasePath.MODULES_DIR
    """Root directory for payload scripts."""

    def __post_init__(self) -> None:
        if self.buffer_size <= 0:
            raise config.ConnectionFailure("buffer_size must be > 0")

        if self.connection_timeout and self.connection_timeout < 0:
            raise config.ConnectionFailure("connection_timeout must be >= 0 or None")

    @property
    def bufsize(self) -> int:
        """Receive buffer size in bytes. Alias for ``buffer_size``."""

        return self.buffer_size

    @property
    def timeout(self) -> float | None:
        """Socket operation timeout in seconds. Alias for ``connection_timeout``."""

        return self.connection_timeout

    def format_operation_script(self, opcode: "config.OperationCode", /, *args: str) -> str | None:
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

        function_name = self.supported_functions.get(opcode)

        if not function_name:
            return None

        return function_name + (" " + " ".join(util.quote(a) for a in args) if args else "")

    def format_client_script(self, host: str, port: int, /) -> str:
        """Read the client script template and substitute connection parameters.

        Args:
            host: The server hostname or IP address to embed in the script.
            port: The port number to embed in the script.

        Returns:
            The fully substituted client script as a string.

        Raises:
            ConnectionFailure: If the template file cannot be read.
        """

        try:
            with self.client_path.open("r") as f:
                client_script_template = f.read()
        except OSError as e:
            raise config.ConnectionFailure(f"Failed to read client script: {e}") from e

        script_kwargs: dict[str, str] = {
            "HOST": host,
            "PORT": str(port),
            "ACKNOWLEDGE": util.convert_bytes_to_hex(self.ack_client_raw),
        }

        return util.format_template(client_script_template, **script_kwargs)


class ShellSocketConnection(interface.IConnection):
    """``IConnection`` implementation over a raw TCP socket.

    Wraps a connected ``socket.socket``, applies ACK-based framing for all
    read/write operations, and manages the library-upload handshake on startup.
    Implements the context manager protocol — the underlying socket is closed
    automatically when the ``with`` block exits.
    """

    def __init__(self, connection: socket, profile: ShellSocketProfile, /) -> None:
        """Bind a live socket to a profile and prepare the session for use.

        Sets the socket timeout from the profile, then pre-render the client
        script by querying the peer address.

        Args:
            connection: An accepted, connected ``socket.socket`` instance.
            profile: The ``ShellSocketProfile`` providing protocol parameters.
        """

        self._profile = profile
        self._connection = connection
        self._timeout = profile.connection_timeout

        if self._timeout is not None:
            self._connection.settimeout(self._timeout)

        remote_host, remote_port = self._connection.getpeername()
        self._client_script = self._profile.format_client_script(remote_host, remote_port)

    def initialize(self) -> None:
        """Perform the initial protocol handshake.

        Sends the concatenated library scripts to the client, then waits for
        the client's ACK sentinel. Raises ``ConnectionFailure`` if the ACK
        is not received within the configured timeout, or if the value is wrong.

        Raises:
            ConnectionFailure: On timeout or invalid client ACK.
        """

        self.write(self._load_library())

        try:
            initial_data = self._connection.recv(self._profile.bufsize)

            if initial_data != self._profile.ack_client_raw:
                raise config.ConnectionFailure("invalid client ACK during session initialization.")
        except TimeoutError as e:
            raise config.ConnectionFailure("timeout waiting for client ACK during session initialization.") from e

    @property
    def client(self) -> interface.IProfile:
        """The ``ShellSocketProfile`` used to configure this connection."""

        return self._profile

    @property
    def client_script(self) -> str:
        """The formatted client bootstrap script, ready to be delivered to the operator.

        Populated during ``__init__`` by substituting the peer address and
        the ACK value into the client script template.
        """

        return self._client_script

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
                chunk = self._connection.recv(self._profile.bufsize)

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

        Both the payload and the sentinel are sent as separate ``send`` calls.

        Args:
            content: The raw bytes payload to transmit.

        Raises:
            ConnectionFailure: On timeout or OS-level I/O error.
        """

        try:
            self._connection.send(content)
            self._connection.send(self._profile.ack_server_raw)
        except TimeoutError as e:
            raise config.ConnectionFailure("Timeout while writing to connection") from e
        except OSError as e:
            raise config.ConnectionFailure(f"Failed to write to connection: {e}") from e

    def close(self) -> None:
        """Close the underlying socket, releasing the OS file descriptor."""

        self._connection.close()

    def _load_library(self) -> bytes:
        """Concatenate all valid library scripts from the configured library directory.

        Files are filtered by ``allowed_library_extensions``. Unreadable files
        are silently skipped. Scripts are joined with newline separators.

        Returns:
            All library file contents joined with ``b'\\n'``.
        """

        all_modules: list[bytes] = []

        for file in self._profile.library_root_directory.iterdir():
            if not file.is_file():
                continue

            if not util.validate_file_extension(file, self._profile.allowed_library_extensions):
                continue

            if module_content := util.try_load_file(file):
                all_modules.append(module_content)

        return b"\n".join(all_modules)

    def _load_payload(self, target_module: str, /) -> bytes:
        """Read a payload script from the configured payload directory.

        Validates that *target_module* resolves to a path inside
        ``payload_root_directory`` (path-traversal guard) before reading.

        Args:
            target_module: Filename of the payload relative to the payload root.

        Returns:
            The raw bytes content of the payload file.

        Raises:
            ConnectionFailure: If the resolved path escapes the payload root,
                or if the file cannot be read.
        """

        payload_filepath = self._profile.payload_root_directory / target_module

        if not util.validate_file_relative(payload_filepath, self._profile.payload_root_directory):
            raise config.ConnectionFailure(f"payload path {payload_filepath} is not relative to the payload root directory")

        try:
            with payload_filepath.open("rb") as f:
                payload_data = f.read()
        except OSError as e:
            raise config.ConnectionFailure(f"Failed to read payload script: {e}") from e

        return payload_data


DEFAULT_SHELL_SOCKET = ShellSocketProfile(
    name="Shell Socket",
    client_path=config.BasePath.CLIENTS_DIR / "shell_socket.sh",
    ack_server_raw=b"\x00",
    ack_client_raw=util.hash_sha256(b"\xba\xdc\x00\xff\xee"),
    allowed_payload_extensions=(".sh",),
    allowed_library_extensions=(".sh",),
)
"""Default ShellSocketProfile instance with typical configuration for a shell socket client."""
