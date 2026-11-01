"""Integration tests verifying LaunchShell execution over PySocketConnection."""

import struct
import threading
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from declusor import command, config, contract, testing

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

    def test_launch_shell__multiple_commands_then_ctrl_c__preserves_connection_for_subsequent_commands(
        self,
        tmp_path: Path,
    ) -> None:
        """Verify LaunchShell handles Ctrl+C cleanly and preserves connection for subsequent commands."""

        client_transport, server_transport = testing.create_memory_transport_pair()
        initial_timeout = 2.0
        connection, processor = self.create_connected_session(tmp_path, server_transport, initial_timeout)

        responses: Mapping[str, bytes] = {
            "id": b"uid=1000(operator) gid=1000(operator)\n",
            "uname -a": b"Linux declusor-node 6.1.0 #1 SMP PREEMPT_DYNAMIC x86_64 GNU/Linux\n",
        }
        interactions = (
            ("id", b"uid=1000(operator)"),
            ("uname -a", b"Linux declusor-node"),
        )

        view = testing.DummyView()
        input_source = testing.PacedInteractiveInputSource(
            interactions,
            view,
            is_idle_predicate=lambda: self.is_connection_idle(connection),
            terminal_exception=KeyboardInterrupt(),
            timeout=3.0,
        )
        session = contract.SessionContext(
            connection=connection,
            view=view,
            plugin_processor=processor,
            input_source=input_source,
        )

        banner = "=== Interactive Remote Shell ==="
        shell_cmd = command.LaunchShell(command.LaunchShellDTO(banner=banner))

        stop_responder = threading.Event()
        responder_thread = threading.Thread(
            target=self.run_mock_client_responder,
            args=(client_transport, responses, stop_responder),
            daemon=True,
        )
        responder_thread.start()

        try:
            session.execute(shell_cmd)

            assert any(banner in msg for msg in view.messages), f"Banner {banner!r} missing from view messages."
            assert "[keyboard interrupt received]" in view.messages, f"Expected '[keyboard interrupt received]' in view messages, got {view.messages}"

            accumulated_output = b"".join(view.binary_data)
            assert b"uid=1000(operator)" in accumulated_output, "Output from 'id' command was not received."
            assert b"Linux declusor-node" in accumulated_output, "Output from 'uname -a' command was not received."

            assert not view.errors, f"Unexpected view errors during shell execution: {view.errors}"
            assert not shell_cmd._task_pool.errors, f"Unexpected task pool errors: {shell_cmd._task_pool.errors}"
            assert connection.state == contract.ConnectionState.CONNECTED, f"Connection state changed unexpectedly: {connection.state}"
            assert connection.timeout == initial_timeout, (
                f"Connection timeout was not restored (expected {initial_timeout}, got {connection.timeout})."
            )

            for thread in shell_cmd._task_pool._threads:
                assert not thread.is_alive(), f"Task pool thread {thread.name} remained alive after shutdown."

            binary_count_before = len(view.binary_data)
            subsequent_cmd = command.ExecuteCommand(command.ExecuteCommandDTO("id"))
            session.execute(subsequent_cmd)

            subsequent_output = b"".join(view.binary_data[binary_count_before:])
            assert b"uid=1000(operator)" in subsequent_output, f"Subsequent 'id' command output was not received: {subsequent_output!r}"
            assert not view.errors, f"Unexpected view errors after subsequent command: {view.errors}"
            assert connection.state == contract.ConnectionState.CONNECTED
            assert connection.timeout == initial_timeout
        finally:
            stop_responder.set()
            responder_thread.join(timeout=1.0)
            client_transport.close()
            server_transport.close()
            connection.close()
