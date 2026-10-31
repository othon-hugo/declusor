"""Integration tests verifying LaunchShell execution over PySocketConnection."""

import struct
import threading
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from declusor import config, contract, testing

import declusor_py_socket as py_socket


class TestPySocketInteractiveShell(testing.InteractiveShellTestSuite[py_socket.PySocketConnection, py_socket.PySocketProcessor]):
    """Cohesive tests verifying LaunchShell execution against real PySocketConnection instances."""

    @pytest.fixture
    def plugin_class(self) -> type[py_socket.PySocketPlugin]:
        """Provide the PySocketPlugin class under test."""

        return py_socket.PySocketPlugin

    @property
    def forbidden_delimiters(self) -> Sequence[bytes]:
        """Delimiters or control tokens that must never leak into raw view output."""

        return ()

    def is_connection_idle(self, connection: py_socket.PySocketConnection) -> bool:
        """Check if PySocketConnection has completed the current command and is ready for input."""

        return connection.is_idle

    def create_connected_session(
        self,
        tmp_path: Path,
        transport: contract.ITransport,
        timeout: float,
    ) -> tuple[py_socket.PySocketConnection, py_socket.PySocketProcessor]:
        """Establish and return a connected PySocketConnection and PySocketProcessor over the given transport."""

        launchers = tmp_path / "launchers"
        launchers.mkdir(parents=True, exist_ok=True)
        (launchers / "py_socket_client.py").write_text("# py_socket client launcher", encoding="utf-8")

        helpers = tmp_path / "helpers"
        helpers.mkdir(parents=True, exist_ok=True)

        modules = tmp_path / "modules"
        modules.mkdir(parents=True, exist_ok=True)

        renderer = py_socket.PySocketRenderer()
        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = py_socket.PySocketProcessor(fs)

        connection = py_socket.PySocketConnection(
            transport,
            renderer,
            processor,
            timeout=timeout,
        )
        connection._state = contract.ConnectionState.CONNECTED

        return connection, processor

    def run_mock_client_responder(
        self,
        client_transport: contract.ITransport,
        responses: Mapping[str, bytes],
        stop_event: threading.Event,
    ) -> None:
        """Run simulated client responder servicing commands until stop_event is signaled."""

        client_transport.timeout = 0.2

        while not stop_event.is_set() and not client_transport.is_closed:
            try:
                header = client_transport.read_exact(5)
            except config.ConnectionTimeoutError:
                continue
            except config.ConnectionClosed:
                break

            channel, length = struct.unpack(">BI", header)

            try:
                payload = client_transport.read_exact(length) if length > 0 else b""
            except config.ConnectionTimeoutError:
                continue
            except config.ConnectionClosed:
                break

            if channel == config.ChannelType.STDIN:
                decoded = payload.decode("utf-8", errors="replace")
                output = b"ok\n"
                for key, val in responses.items():
                    if key in decoded:
                        output = val
                        break

                try:
                    stdout_frame = struct.pack(">BI", config.ChannelType.STDOUT, len(output)) + output
                    client_transport.write(stdout_frame)
                    exit_frame = struct.pack(">BI", config.ChannelType.PROCESS_EXIT, 0)
                    client_transport.write(exit_frame)
                except (config.ConnectionClosed, config.ConnectionError):
                    break

    def run_mock_client_abrupt_disconnect(
        self,
        client_transport: contract.ITransport,
    ) -> None:
        """Simulate client-side abrupt network disconnect during an active shell session."""

        client_transport.timeout = 1.0

        while not client_transport.is_closed:
            try:
                header = client_transport.read_exact(5)
            except (config.ConnectionTimeoutError, config.ConnectionClosed):
                break

            channel, length = struct.unpack(">BI", header)

            try:
                _ = client_transport.read_exact(length) if length > 0 else b""
            except (config.ConnectionTimeoutError, config.ConnectionClosed):
                break

            if channel == config.ChannelType.STDIN:
                try:
                    partial = b"starting background operation with extensive logging...\n"
                    stdout_frame = struct.pack(">BI", config.ChannelType.STDOUT, len(partial)) + partial
                    client_transport.write(stdout_frame)
                except (config.ConnectionClosed, config.ConnectionError):
                    pass
                finally:
                    client_transport.close()
                break
