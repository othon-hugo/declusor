from dataclasses import dataclass, field
from pathlib import Path
from socket import socket
from typing import Generator

from declusor import config, interface, util


@dataclass(frozen=True)
class ShellSocketProfile(interface.IProfile):
    """Configuration data for a shell socket client."""

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
        return self.buffer_size

    @property
    def timeout(self) -> float | None:
        return self.connection_timeout

    def format_operation_script(self, opcode: "config.OperationCode", /, *args: str) -> str | None:
        function_name = self.supported_functions.get(opcode)

        if not function_name:
            return None

        return function_name + (" " + " ".join(util.quote(a) for a in args) if args else "")

    def format_client_script(self, host: str, port: int, /) -> str:
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
    """Manages a session over a socket connection, handling reading and writing of data."""

    def __init__(self, connection: socket, profile: ShellSocketProfile, /) -> None:
        """Initialize the Session using the provided socket connection and configuration.

        Args:
            connection: The socket connection.
            profile: The ShellSocketProfile containing configuration for the session.
        """

        self._profile = profile
        self._connection = connection
        self._timeout = profile.connection_timeout

        if self._timeout is not None:
            self._connection.settimeout(self._timeout)

        remote_host, remote_port = self._connection.getpeername()
        self._client_script = self._format_client_script(remote_host, remote_port)

    def initialize(self) -> None:
        """Perform initial handshake/setup."""

        self.write(self._load_library())

        try:
            initial_data = self._connection.recv(self._profile.buffer_size)

            if initial_data != self._profile.ack_client_raw:
                raise config.ConnectionFailure("invalid client ACK during session initialization.")
        except TimeoutError as exc:
            raise config.ConnectionFailure("timeout waiting for client ACK during session initialization.") from exc

    @property
    def client(self) -> interface.IProfile:
        return self._profile

    @property
    def client_script(self) -> str:
        """Read the client script content."""

        return self._client_script

    @property
    def timeout(self) -> float | None:
        """Timeout for socket operations."""

        return self._timeout

    @timeout.setter
    def timeout(self, value: float | None, /) -> None:
        """Set the timeout for socket operations."""

        self._timeout = value
        self._connection.settimeout(self._timeout)

    def read(self) -> Generator[bytes, None, None]:
        """Read data from the connection until the client ACK is received.

        Yields chunks of data as they arrive, excluding the ACK. Only keeps a small
        buffer (size of ACK) to detect when transmission is complete.
        """

        ack, ack_len = self._profile.ack_client_raw, len(self._profile.ack_client_raw)
        buffer = bytearray()

        while True:
            try:
                chunk = self._connection.recv(self._profile.buffer_size)

                if not chunk:
                    # ConnectionResetError inherits from OSError, so it is
                    # caught by the except OSError handler below and wrapped
                    # into ConnectionFailure.
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

            except TimeoutError as exc:
                raise config.ConnectionFailure("Timeout while reading from connection") from exc
            except OSError as exc:
                raise config.ConnectionFailure(f"Failed to read from connection: {exc}") from exc

    def write(self, content: bytes, /) -> None:
        """Write data to the connection followed by the client ACK.

        Args:
            content: The bytes to send.
        """

        try:
            self._connection.send(content)
            self._connection.send(self._profile.ack_server_raw)
        except TimeoutError as exc:
            raise config.ConnectionFailure("Timeout while writing to connection") from exc
        except OSError as exc:
            raise config.ConnectionFailure(f"Failed to write to connection: {exc}") from exc

    def close(self) -> None:
        """Close the session socket."""

        self._connection.close()

    def _load_library(self) -> bytes:
        """Load all library scripts from the configured library directory."""

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
        """Load a payload script from the configured payload directory."""

        payload_filepath = self._profile.payload_root_directory / target_module

        if not util.validate_file_relative(payload_filepath, self._profile.payload_root_directory):
            raise config.ConnectionFailure(f"payload path {payload_filepath} is not relative to the payload root directory")

        try:
            with payload_filepath.open("rb") as f:
                payload_data = f.read()
        except OSError as e:
            raise config.ConnectionFailure(f"Failed to read payload script: {e}") from e

        return payload_data

    def _format_client_script(self, host: str, port: int, /) -> str:
        """Load and format the client script template with connection details."""

        try:
            with self._profile.client_path.open("r") as f:
                client_script_template = f.read()
        except OSError as e:
            raise config.ConnectionFailure(f"Failed to read client script: {e}") from e

        script_kwargs: dict[str, str] = {
            "HOST": host,
            "PORT": str(port),
            "ACKNOWLEDGE": util.convert_bytes_to_hex(self._profile.ack_client_raw),
        }

        return util.format_template(client_script_template, **script_kwargs)


DEFAULT_SHELL_SOCKET = ShellSocketProfile(
    name="Shell Socket",
    client_path=config.BasePath.CLIENTS_DIR / "shell_socket.sh",
    ack_server_raw=b"\x00",
    ack_client_raw=b"\xba\xdc\x00\xff\xee",
    allowed_payload_extensions=(".sh",),
    allowed_library_extensions=(".sh",),
)
"""Default ShellSocketProfile instance with typical configuration for a shell socket client."""
