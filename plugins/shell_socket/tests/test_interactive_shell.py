"""Integration tests verifying LaunchShell execution over ShellSocketConnection."""

import threading
from collections.abc import Mapping, Sequence
from pathlib import Path

import declusor_shell_socket as shell_socket
import pytest

from declusor import config, contract, testing


class TestShellSocketInteractiveShell(testing.InteractiveShellTestSuite[shell_socket.ShellSocketConnection, shell_socket.ShellSocketProcessor]):
    """Cohesive tests verifying LaunchShell execution against real ShellSocketConnection instances."""

    @pytest.fixture
    def plugin_class(self) -> type[shell_socket.ShellSocketPlugin]:
        """Provide the ShellSocketPlugin class under test."""

        return shell_socket.ShellSocketPlugin

    @property
    def forbidden_delimiters(self) -> Sequence[bytes]:
        """Delimiters or control tokens that must never leak into raw view output."""

        return (b"__DECLUSOR_EOF_",)

    def is_connection_idle(self, connection: shell_socket.ShellSocketConnection) -> bool:
        """Check if ShellSocketConnection has completed the current command and is ready for input."""

        return connection.current_nonce is None

    def create_connected_session(
        self,
        tmp_path: Path,
        transport: contract.ITransport,
        timeout: float,
    ) -> tuple[shell_socket.ShellSocketConnection, shell_socket.ShellSocketProcessor]:
        """Establish and return a connected ShellSocketConnection and ShellSocketProcessor over the given transport."""

        launchers = tmp_path / "launchers"
        launchers.mkdir(parents=True, exist_ok=True)
        (launchers / "shell_socket_client.sh").write_text("$HOST:$PORT", encoding="utf-8")

        helpers = tmp_path / "helpers"
        helpers.mkdir(parents=True, exist_ok=True)
        modules = tmp_path / "modules"
        modules.mkdir(parents=True, exist_ok=True)

        renderer = shell_socket.ShellSocketRenderer()
        fs = contract.PluginFilesystem.from_root(tmp_path)
        processor = shell_socket.ShellSocketProcessor(fs)

        connection = shell_socket.ShellSocketConnection(
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

        buffer = bytearray()
        client_transport.timeout = 0.2

        while not stop_event.is_set() and not client_transport.is_closed:
            try:
                chunk = client_transport.read(4096)
            except config.ConnectionTimeoutError:
                continue
            except config.ConnectionClosed:
                break

            if not chunk:
                break

            buffer.extend(chunk)

            while b"\x00" in buffer:
                first_null = buffer.find(b"\x00")
                second_null = buffer.find(b"\x00", first_null + 1)
                if second_null == -1:
                    break

                nonce_bytes = bytes(buffer[:first_null])
                command_bytes = bytes(buffer[first_null + 1 : second_null])
                del buffer[: second_null + 1]

                cmd_str = command_bytes.decode("utf-8", errors="replace").strip()
                payload_output = responses.get(cmd_str, f"{cmd_str}: done\n".encode())
                delim = f"__DECLUSOR_EOF_{nonce_bytes.decode('ascii', errors='replace')}__\n".encode("ascii")

                try:
                    half = len(payload_output) // 2
                    client_transport.write(payload_output[:half])
                    client_transport.write(payload_output[half:])
                    split_point = len(self.forbidden_delimiters[0])
                    client_transport.write(delim[:split_point])
                    client_transport.write(delim[split_point:])
                except (config.ConnectionClosed, config.ConnectionError):
                    return

    def run_mock_client_abrupt_disconnect(
        self,
        client_transport: contract.ITransport,
    ) -> None:
        """Simulate client-side abrupt network disconnect during an active shell session."""

        buffer = bytearray()
        client_transport.timeout = 0.2

        while not client_transport.is_closed:
            try:
                chunk = client_transport.read(4096)
            except config.ConnectionTimeoutError:
                continue
            except config.ConnectionClosed:
                break

            if not chunk:
                break

            buffer.extend(chunk)

            if b"\x00" in buffer:
                first_null = buffer.find(b"\x00")
                second_null = buffer.find(b"\x00", first_null + 1)
                if second_null != -1:
                    try:
                        client_transport.write(b"starting background operation with extensive logging output that exceeds the threshold...\n")
                    except (config.ConnectionClosed, config.ConnectionError):
                        pass
                    finally:
                        client_transport.close()
                    break
