"""Reusable, fully-typed test doubles implementing Declusor contracts.

Provides mock-free, deterministic test doubles for consoles, connections,
profiles, file stores, runtimes, plugins, routers, and transport sockets.
"""

from collections.abc import Generator, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from socket import socket
from typing import Self

from declusor import config, util
from declusor.config import DataPaths, OperationCode
from declusor.contract import (
    ClientConfig,
    ConnectionState,
    Controller,
    IClientFileStore,
    IClientPlugin,
    IClientRuntime,
    ICommand,
    IConnection,
    IConnectionProfile,
    IConsole,
    IRouter,
    SessionContext,
)


class DummyConsole(IConsole):
    """Fully-typed in-memory console capturing all output and simulating input."""

    def __init__(self, inputs: Sequence[str] | None = None) -> None:
        self._inputs: list[str] = list(inputs) if inputs is not None else []
        self.input_exception: BaseException | None = None
        self.messages: list[str] = []
        self.binary_data: list[bytes] = []
        self.errors: list[str | BaseException] = []
        self.warnings: list[str | BaseException] = []
        self.prompts: list[str] = []
        self.history_files: list[Path] = []
        self.configured_completers: list[list[str]] = []

    def feed_inputs(self, *lines: str) -> None:
        """Enqueue simulated input lines for read_line and read_stripped_line."""
        self._inputs.extend(lines)

    def setup_completer(self, commands: Sequence[str], /) -> None:
        """Capture registered completion commands."""
        self.configured_completers.append(list(commands))

    def enable_history(self, history_file: Path, /) -> None:
        """Record the configured history file path."""
        self.history_files.append(history_file)

    def read_line(self, prompt: str = "", /) -> str:
        """Return the next queued input line or newline if queue is empty."""
        self.prompts.append(prompt)
        if self.input_exception is not None:
            exc = self.input_exception
            self.input_exception = None
            raise exc
        if not self._inputs:
            return "\n"
        line = self._inputs.pop(0)
        return line if line.endswith("\n") else f"{line}\n"

    def read_stripped_line(self, prompt: str = "", /) -> str:
        """Return the next queued stripped input line or empty string if queue is empty."""
        self.prompts.append(prompt)
        if self.input_exception is not None:
            exc = self.input_exception
            self.input_exception = None
            raise exc
        if not self._inputs:
            return ""
        return self._inputs.pop(0).strip()

    def write_message(self, message: str, /) -> None:
        """Capture plain text output message."""
        self.messages.append(message)

    def write_binary_data(self, message: bytes, /) -> None:
        """Capture raw binary output payload."""
        self.binary_data.append(message)

    def write_error_message(self, message: str | BaseException, /) -> None:
        """Capture error output message or exception."""
        self.errors.append(message)

    def write_warning_message(self, message: str | BaseException, /) -> None:
        """Capture warning output message or exception."""
        self.warnings.append(message)


class DummyConnectionProfile(IConnectionProfile):
    """Fully-typed in-memory connection profile with configurable operation command rendering."""

    def __init__(
        self,
        name: str = "dummy_profile",
        buffer_size: int = 4096,
        timeout: float | None = 5.0,
        rendered_commands: dict[OperationCode, str | None] | None = None,
    ) -> None:
        self._name = name
        self._buffer_size = buffer_size
        self._timeout = timeout
        self.rendered_commands: dict[OperationCode, str | None] = dict(rendered_commands) if rendered_commands is not None else {}
        self.render_calls: list[tuple[OperationCode, tuple[str, ...]]] = []

    @property
    def default_buffer_size(self) -> int:
        return self._buffer_size

    @property
    def default_timeout(self) -> float | None:
        return self._timeout

    def set_rendered_command(self, opcode: OperationCode, rendered: str | None) -> None:
        """Configure the returned rendered command string for an operation code."""
        self.rendered_commands[opcode] = rendered

    def render_operation_command(self, opcode: OperationCode, /, *args: str) -> str | None:
        """Return configured rendered command or a deterministic default string."""
        self.render_calls.append((opcode, args))
        if opcode in self.rendered_commands:
            return self.rendered_commands[opcode]
        args_str = f" {' '.join(args)}" if args else ""
        return f"{opcode.value}{args_str}"


class DummyConnection(IConnection):
    """Fully-typed test double for active client network connections."""

    def __init__(
        self,
        client: IConnectionProfile | None = None,
        incoming_chunks: Sequence[bytes] | None = None,
        initial_state: ConnectionState = ConnectionState.CONNECTED,
    ) -> None:
        self._client: IConnectionProfile = client or DummyConnectionProfile()
        self._state: ConnectionState = initial_state
        self._timeout: float | None = None
        self.written: list[bytes] = []
        self.incoming_chunks: list[bytes] = list(incoming_chunks) if incoming_chunks is not None else [b"chunk1\n", b"chunk2\n"]
        self.initialize_called: bool = False
        self.closed: bool = False
        self.initialize_error: BaseException | None = None
        self.write_error: BaseException | None = None
        self.read_error: BaseException | None = None

    @property
    def state(self) -> ConnectionState:
        return self._state

    @state.setter
    def state(self, value: ConnectionState) -> None:
        self._state = value

    @property
    def client(self) -> IConnectionProfile:
        return self._client

    @property
    def timeout(self) -> float | None:
        return self._timeout

    @timeout.setter
    def timeout(self, value: float | None, /) -> None:
        self._timeout = value

    def initialize(self) -> None:
        """Simulate protocol handshake."""
        self.initialize_called = True
        if self.initialize_error is not None:
            raise self.initialize_error
        self._state = ConnectionState.CONNECTED

    def read(self) -> Generator[bytes, None, None]:
        """Yield simulated incoming bytes chunks."""
        if self.read_error is not None:
            raise self.read_error
        yield from self.incoming_chunks

    def write(self, content: bytes, /) -> None:
        """Record transmitted bytes."""
        if self.write_error is not None:
            raise self.write_error
        self.written.append(content)

    def close(self) -> None:
        """Simulate closing transport resources."""
        self.closed = True
        self._state = ConnectionState.CLOSED

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        self.close()


class DummyClientFileStore(IClientFileStore):
    """Fully-typed in-memory file store for client scripts, libraries, and modules."""

    def __init__(
        self,
        script_template: str = "#!/bin/sh\n# Host: {host}:{port}\n# Ack: {acknowledge}",
        library_bytes: bytes = b"dummy_library_payload",
        modules: dict[str, bytes] | None = None,
    ) -> None:
        self.script_template: str = script_template
        self.library_bytes: bytes = library_bytes
        self.modules: dict[str, bytes] = dict(modules) if modules is not None else {}
        self.load_module_calls: list[str] = []
        self.load_library_calls: int = 0
        self.render_calls: list[tuple[str, int, bytes]] = []

    def set_module(self, name: str, content: bytes) -> None:
        """Register a module name and content payload."""
        self.modules[name] = content

    def render_client_script(self, host: str, port: int, acknowledge: bytes, /) -> str:
        """Render client script from configured template."""
        self.render_calls.append((host, port, acknowledge))
        return self.script_template.format(host=host, port=port, acknowledge=acknowledge.hex())

    def load_library(self) -> bytes:
        """Return configured library payload."""
        self.load_library_calls += 1
        return self.library_bytes

    def load_module(self, module_name: str, /) -> bytes:
        """Return configured or synthesised module payload."""
        self.load_module_calls.append(module_name)
        if module_name in self.modules:
            return self.modules[module_name]
        return f"module_bytes:{module_name}".encode()


class DummyClientRuntime(IClientRuntime):
    """Fully-typed client runtime producing configured connections and scripts."""

    def __init__(
        self,
        file_store: IClientFileStore | None = None,
        client_script: str = "#!/bin/sh\necho dummy",
        connection_to_return: IConnection | None = None,
    ) -> None:
        self._file_store: IClientFileStore = file_store or DummyClientFileStore()
        self._client_script: str = client_script
        self.connection_to_return: IConnection | None = connection_to_return
        self.created_connections: list[IConnection] = []

    @property
    def client_files(self) -> IClientFileStore:
        return self._file_store

    @property
    def client_script(self) -> str:
        return self._client_script

    def create_connection(self, connection: socket, /) -> IConnection:
        """Return configured connection or new DummyConnection instance."""
        conn = self.connection_to_return or DummyConnection()
        self.created_connections.append(conn)
        return conn


class DummyClientPlugin(IClientPlugin):
    """Fully-typed client plugin implementing the IClientPlugin extension point."""

    name: str = "dummy"
    description: str = "Dummy client plugin for unit tests"
    version: str = "1.0.0"
    author: str = "Test Suite"

    configured_parsers: list[util.Parser] = []
    runtime_instance: IClientRuntime | None = None
    validation_error: BaseException | None = None

    @classmethod
    def reset(cls) -> None:
        """Reset static test tracking state."""
        cls.configured_parsers.clear()
        cls.runtime_instance = None
        cls.validation_error = None

    @classmethod
    def configure_parser(cls, parser: util.Parser, /) -> None:
        cls.configured_parsers.append(parser)

    @classmethod
    def build_config(cls, args: util.Namespace, data_paths: DataPaths, /) -> ClientConfig:
        return ClientConfig(
            kind=cls.name,
            host=getattr(args, "host", "127.0.0.1"),
            port=getattr(args, "port", 9000),
            data_paths=data_paths,
        )

    @classmethod
    def validate(cls, client_config: ClientConfig, /) -> None:
        if cls.validation_error is not None:
            raise cls.validation_error

    @classmethod
    def build_runtime(cls, client_config: ClientConfig, /) -> IClientRuntime:
        return cls.runtime_instance or DummyClientRuntime()


class DummyRouter(IRouter):
    """Fully-typed router supporting deterministic route registration and dispatch."""

    def __init__(self) -> None:
        self._routes: dict[str, Controller] = {}
        self._usage: dict[str, str] = {}
        self.locate_calls: list[str] = []

    @property
    def routes(self) -> tuple[str, ...]:
        return tuple(self._routes.keys())

    @property
    def documentation(self) -> str:
        return "\n".join(f"{r}: {self.get_route_usage(r)}" for r in self._routes)

    def get_route_usage(self, route: str, /) -> str:
        r = route.strip()
        if r in self._usage:
            return self._usage[r]
        if r in self._routes:
            doc = getattr(self._routes[r], "__doc__", None)
            if isinstance(doc, str) and doc.strip():
                return str(doc.strip().splitlines()[0])
        return ""

    def set_route_usage(self, route: str, usage: str) -> None:
        """Override the usage string for a specific route."""
        self._usage[route.strip()] = usage

    def connect(self, route: str, controller: Controller, /) -> None:
        r = route.strip()
        if r in self._routes:
            raise ValueError(f"route already exists: {r}")
        self._routes[r] = controller

    def locate(self, route: str, /) -> Controller:
        r = route.strip()
        self.locate_calls.append(r)
        if r not in self._routes:
            raise config.RouterError(r, "unknown route")
        return self._routes[r]


class DummySocket:
    """Fully-typed fake socket object simulating OS transport without system resources."""

    def __init__(
        self,
        incoming_bytes: bytes = b"",
        peer_name: tuple[str, int] = ("127.0.0.1", 9000),
        fileno_val: int = 42,
    ) -> None:
        self._incoming: bytearray = bytearray(incoming_bytes)
        self._sent: bytearray = bytearray()
        self.peer_name: tuple[str, int] = peer_name
        self.fileno_val: int = fileno_val
        self.closed: bool = False
        self.timeout: float | None = None

    @property
    def sent_bytes(self) -> bytes:
        """Read-only view of bytes sent through this socket."""
        return bytes(self._sent)

    def feed_bytes(self, data: bytes) -> None:
        """Enqueue simulated incoming data to be read via recv."""
        self._incoming.extend(data)

    def recv(self, bufsize: int, /) -> bytes:
        """Read up to bufsize bytes from incoming buffer."""
        chunk = bytes(self._incoming[:bufsize])
        del self._incoming[:bufsize]
        return chunk

    def sendall(self, data: bytes, /) -> None:
        """Record all sent bytes."""
        self._sent.extend(data)

    def send(self, data: bytes, /) -> int:
        """Record all sent bytes and return count."""
        self._sent.extend(data)
        return len(data)

    def getpeername(self) -> tuple[str, int]:
        """Return configured peer address tuple."""
        return self.peer_name

    def settimeout(self, timeout: float | None, /) -> None:
        """Set timeout value."""
        self.timeout = timeout

    def close(self) -> None:
        """Mark socket as closed."""
        self.closed = True

    def fileno(self) -> int:
        """Return configured file descriptor number."""
        return self.fileno_val

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        self.close()


@dataclass
class DummyCommand(ICommand):
    """Command double tracking execution sequencing for lifecycle testing."""

    call_sequence: list[str] = field(default_factory=list)
    send_request_error: BaseException | None = None
    read_response_error: BaseException | None = None

    def send_request(self, session: SessionContext) -> None:
        self.call_sequence.append("send_request")
        if self.send_request_error is not None:
            raise self.send_request_error

    def read_response(self, session: SessionContext) -> None:
        self.call_sequence.append("read_response")
        if self.read_response_error is not None:
            raise self.read_response_error
