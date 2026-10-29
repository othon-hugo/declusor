"""Integration tests verifying LaunchShell execution over ShellSocketConnection."""

import contextlib
import threading
import time
from collections.abc import Sequence
from pathlib import Path

import declusor_shell_socket as shell_socket

from declusor import command, config, contract, testing, util


class PacedInteractiveInputSource(testing.DummyInputSource):
    """Input source double that paces queued commands against view output reception."""

    def __init__(
        self,
        interactions: Sequence[tuple[str, bytes]],
        view: testing.DummyView,
        connection: shell_socket.ShellSocketConnection,
        *,
        terminal_exception: BaseException | None = None,
    ) -> None:
        """Initialize with interaction tuples of command and expected response substring."""

        super().__init__()
        self._interactions: list[tuple[str, bytes]] = list(interactions)
        self._view = view
        self._connection = connection
        self._connection = connection
        self._terminal_exception: BaseException = terminal_exception if terminal_exception is not None else KeyboardInterrupt()
        self._last_expected: bytes | None = None
        self._view_cursor: int = 0

    def read_raw(self, prompt: str = "", /) -> str:
        """Return next command once preceding command output and delimiter have completed."""

        self.prompts.append(prompt)

        if self._last_expected is not None:
            self._wait_for_view_content(self._last_expected)
            self._last_expected = None

        if self._interactions:
            cmd, expected = self._interactions.pop(0)
            self._last_expected = expected
            return cmd if cmd.endswith("\n") else f"{cmd}\n"

        raise self._terminal_exception

    def _wait_for_view_content(self, expected: bytes, timeout: float = 3.0) -> None:
        """Poll view buffer until expected byte sequence appears and command envelope completes."""

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            accumulated = b"".join(self._view.binary_data[self._view_cursor :])
            if expected in accumulated and self._connection.current_nonce is None:
                self._view_cursor = len(self._view.binary_data)
                return
            time.sleep(0.005)

        raise TimeoutError(f"Timed out waiting for expected view output: {expected!r}")


class DisconnectAwareInputSource(testing.DummyInputSource):
    """Input source double that yields queued commands and unblocks on cooperative stop flag."""

    def __init__(
        self,
        inputs: Sequence[str] | None = None,
        *,
        stop_event: util.TaskEvent | None = None,
        timeout: float = 3.0,
        input_exception: BaseException | None = None,
    ) -> None:
        """Initialize with queued inputs, cooperative stop event, and timeout limit."""

        super().__init__(inputs)
        self._stop_event = stop_event
        self._timeout = timeout
        self.input_exception = input_exception

    def read_raw(self, prompt: str = "", /) -> str:
        """Return next queued command line, raise exception, or wait for cooperative cancellation."""

        self.prompts.append(prompt)

        if self.input_exception is not None:
            exc = self.input_exception
            self.input_exception = None
            raise exc

        if self._inputs:
            line = self._inputs.pop(0)
            return line if line.endswith("\n") else f"{line}\n"

        if self._stop_event is not None:
            if not self._stop_event.wait(timeout=self._timeout):
                raise TimeoutError(f"Timed out waiting {self._timeout}s for stop event.")
            return ""

        raise EOFError("No further input available and no stop event registered.")


def _create_shell_connection(
    tmp_path: Path,
    transport: contract.ITransport,
    *,
    timeout: float | None = 15.0,
) -> tuple[shell_socket.ShellSocketConnection, shell_socket.ShellSocketProcessor]:
    """Instantiate a connected ShellSocketConnection backed by the provided transport."""

    launchers = tmp_path / "launchers"
    launchers.mkdir(exist_ok=True)
    (launchers / "shell_socket_client.sh").write_text("$HOST:$PORT", encoding="utf-8")

    helpers = tmp_path / "helpers"
    helpers.mkdir(exist_ok=True)
    modules = tmp_path / "modules"
    modules.mkdir(exist_ok=True)

    renderer = shell_socket.ShellSocketRenderer()
    fs = contract.PluginFilesystem.from_root(tmp_path)
    files = shell_socket.ShellSocketProcessor(fs)

    connection = shell_socket.ShellSocketConnection(
        transport,
        renderer,
        files,
        fixed_nonce=None,
        timeout=timeout,
    )
    connection._state = contract.ConnectionState.CONNECTED

    return connection, files


class TestShellSocketInteractiveShell:
    """Cohesive tests verifying LaunchShell execution against real ShellSocketConnection instances."""

    def test_launch_shell__multiple_interactive_commands__streams_outputs_without_delimiter_leak(
        self,
        tmp_path: Path,
    ) -> None:
        """Verify sequential commands stream multi-chunk outputs cleanly without leaking delimiters."""

        trans_client, trans_server = testing.create_memory_transport_pair()
        initial_timeout = 15.0
        connection, files = _create_shell_connection(tmp_path, trans_server, timeout=initial_timeout)
        view = testing.DummyView()

        long_output_segment = b"line_stream_data_chunk_exceeding_keep_len_" * 4 + b"\n"
        interactions = [
            ("id\n", b"uid=1000(dev) gid=1000(dev)\n"),
            ("uname -s\n", b"Linux\n"),
            ("echo test_shell_output\n", long_output_segment),
        ]
        input_source = PacedInteractiveInputSource(interactions, view, connection)
        session = contract.SessionContext(
            connection=connection,
            view=view,
            input_source=input_source,
            plugin_processor=files,
        )

        responses: dict[str, bytes] = {
            "id": b"uid=1000(dev) gid=1000(dev)\n",
            "uname -s": b"Linux\n",
            "echo test_shell_output": long_output_segment,
        }
        stop_mock_client = threading.Event()

        def _mock_client_responder() -> None:
            buffer = bytearray()
            trans_client.timeout = 0.2

            while not stop_mock_client.is_set() and not trans_client.is_closed:
                try:
                    chunk = trans_client.read(4096)
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
                    delim = f"__DECLUSOR_EOF_{nonce_bytes.decode('ascii')}__\n".encode("ascii")

                    try:
                        # Write output in multiple chunks and split the delimiter to verify streaming without delimiter leak
                        half = len(payload_output) // 2
                        trans_client.write(payload_output[:half])
                        trans_client.write(payload_output[half:])
                        trans_client.write(delim[:15])  # Prefix "__DECLUSOR_EOF_"
                        trans_client.write(delim[15:])
                    except config.ConnectionClosed:
                        break

        client_thread = threading.Thread(
            target=_mock_client_responder,
            name="mock_client_responder",
            daemon=True,
        )
        client_thread.start()

        cmd = command.LaunchShell(command.LaunchShellDTO(banner="=== Interactive Remote Shell ==="))

        try:
            cmd.execute(session)
        finally:
            stop_mock_client.set()
            trans_client.close()
            client_thread.join(timeout=2.0)
            connection.close()

        accumulated_output = b"".join(view.binary_data)
        assert b"uid=1000(dev) gid=1000(dev)\n" in accumulated_output
        assert b"Linux\n" in accumulated_output
        assert long_output_segment in accumulated_output
        assert b"__DECLUSOR_EOF_" not in accumulated_output
        assert len(view.binary_data) > len(interactions)
        assert "=== Interactive Remote Shell ===" in view.messages
        assert "[keyboard interrupt received]" in view.messages
        assert len(view.errors) == 0
        assert len(cmd._task_pool.errors) == 0
        assert cmd._stop_event.is_set()
        assert not client_thread.is_alive()
        assert all(not thread.is_alive() for thread in cmd._task_pool._threads)
        assert connection.timeout == initial_timeout

    def test_launch_shell__immediate_keyboard_interrupt_before_input__exits_cleanly_without_error(
        self,
        tmp_path: Path,
    ) -> None:
        """Verify immediate KeyboardInterrupt cleanly stops background streaming without errors."""

        trans_client, trans_server = testing.create_memory_transport_pair()
        initial_timeout = 12.0
        connection, files = _create_shell_connection(tmp_path, trans_server, timeout=initial_timeout)
        view = testing.DummyView()

        input_source = DisconnectAwareInputSource(input_exception=KeyboardInterrupt())

        session = contract.SessionContext(
            connection=connection,
            view=view,
            input_source=input_source,
            plugin_processor=files,
        )

        banner = "=== Interactive Remote Shell ==="
        cmd = command.LaunchShell(command.LaunchShellDTO(banner=banner))

        try:
            cmd.execute(session)
            assert connection.state == contract.ConnectionState.CONNECTED
        finally:
            trans_client.close()
            connection.close()

        assert banner in view.messages
        assert "[keyboard interrupt received]" in view.messages
        assert len(view.errors) == 0
        assert len(cmd._task_pool.errors) == 0
        assert len(view.binary_data) == 0
        assert cmd._stop_event.is_set()
        assert all(not thread.is_alive() for thread in cmd._task_pool._threads)
        assert connection.timeout == initial_timeout

    def test_launch_shell__client_disconnects_during_command__terminates_gracefully(
        self,
        tmp_path: Path,
    ) -> None:
        """Verify client disconnection mid-stream sets stop event and cleanly shuts down session."""

        trans_client, trans_server = testing.create_memory_transport_pair()
        initial_timeout = 10.0
        connection, files = _create_shell_connection(tmp_path, trans_server, timeout=initial_timeout)
        view = testing.DummyView()

        cmd = command.LaunchShell(command.LaunchShellDTO())
        input_source = DisconnectAwareInputSource(
            inputs=["long_running_task\n"],
            stop_event=cmd._stop_event,
        )
        session = contract.SessionContext(
            connection=connection,
            view=view,
            input_source=input_source,
            plugin_processor=files,
        )

        def _mock_abrupt_disconnect_client() -> None:
            buffer = bytearray()
            trans_client.timeout = 1.0

            while not trans_client.is_closed:
                try:
                    chunk = trans_client.read(4096)
                except (config.ConnectionTimeoutError, config.ConnectionClosed):
                    break

                if not chunk:
                    break

                buffer.extend(chunk)

                if b"\x00" in buffer:
                    first_null = buffer.find(b"\x00")
                    second_null = buffer.find(b"\x00", first_null + 1)
                    if second_null != -1:
                        # Stream partial chunk exceeding keep_len before abruptly disconnecting
                        with contextlib.suppress(config.ConnectionClosed):
                            trans_client.write(b"starting background operation with extensive logging output that exceeds the threshold...\n")
                        trans_client.close()
                        break

        client_thread = threading.Thread(
            target=_mock_abrupt_disconnect_client,
            name="mock_disconnect_client",
            daemon=True,
        )
        client_thread.start()

        try:
            cmd.execute(session)
        finally:
            trans_client.close()
            client_thread.join(timeout=2.0)
            connection.close()

        accumulated_output = b"".join(view.binary_data)
        assert b"starting background operation" in accumulated_output
        assert b"__DECLUSOR_EOF_" not in accumulated_output
        assert len(view.errors) == 0
        assert len(cmd._task_pool.errors) == 0
        assert cmd._stop_event.is_set()
        assert not client_thread.is_alive()
        assert all(not thread.is_alive() for thread in cmd._task_pool._threads)
        assert connection.timeout == initial_timeout
