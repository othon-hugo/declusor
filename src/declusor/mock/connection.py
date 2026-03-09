from collections.abc import Generator
from pathlib import Path
from typing import Any

from declusor import interface, config


class MockConnectionProfile(interface.IConnectionProfile):
    """A mock implementation of IConnectionProfile for testing."""

    operation_command = "static_operation_command_example"
    """A static operation command that will be returned by the ``render_operation_command`` method."""

    client_script = "static_client_script_example"
    """A static client script that will be returned by the ``render_client_script`` method."""

    supported_opcodes: dict[config.OperationCode, str] = {
        config.OperationCode.STORE_FILE: "STATIC_STORE_FILE_EXAMPLE",
        config.OperationCode.EXEC_FILE: "STATIC_EXEC_FILE_EXAMPLE",
    }
    """A mapping of supported operation codes to their corresponding function names for script generation."""

    def __init__(self) -> None:
        self._default_buffer_size = 4096
        self._default_timeout = 1.0

        self.library_paths_to_yield: list["Path"] = []

    @property
    def default_buffer_size(self) -> int:
        return self._default_buffer_size

    @property
    def default_timeout(self) -> float | None:
        return self._default_timeout

    def iter_library_paths(self) -> Generator["Path", None, None]:
        yield from self.library_paths_to_yield

    def resolve_module_path(self, module_filename: str, /) -> "Path":
        return Path(module_filename)

    def render_operation_command(self, opcode: "config.OperationCode", /, *args: str) -> str | None:
        if opcode not in self.supported_opcodes:
            return None

        return self.operation_command

    def render_client_script(self, host: str, port: int, /) -> str:
        return self.client_script


class MockConnection(interface.IConnection):
    """A mock implementation of IConnection for testing."""

    def __init__(self, profile: "interface.IConnectionProfile") -> None:
        self._client = profile
        self._timeout = profile.default_timeout

        self.initialize_called = False
        self.close_called = False
        self.data_to_read: list[bytes] = []
        self.written_data: list[bytes] = []

    @property
    def client(self) -> "interface.IConnectionProfile":
        return self._client

    @property
    def timeout(self) -> float | None:
        return self._timeout

    @timeout.setter
    def timeout(self, value: float | None, /) -> None:
        self._timeout = value

    def initialize(self) -> None:
        self.initialize_called = True

    def read(self) -> Generator[bytes, None, None]:
        yield from self.data_to_read

    def write(self, content: bytes, /) -> None:
        self.written_data.append(content)

    def close(self) -> None:
        self.close_called = True
