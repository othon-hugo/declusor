"""Unit tests for LaunchShellDTO and LaunchShell in declusor.command."""

from collections.abc import Generator, Sequence
from dataclasses import FrozenInstanceError

import pytest

from declusor import config, contract, testing, util
from declusor.command.launch_shell import LaunchShell, LaunchShellDTO


class ScriptedShellInputSource(testing.DummyInputSource):
    """Input source double that returns queued lines and raises a terminal exception on exhaustion."""

    def __init__(
        self,
        inputs: Sequence[str] | None = None,
        *,
        terminal_exception: BaseException | None = None,
    ) -> None:
        """Initialize scripted input source with queued lines and optional terminal exception."""

        super().__init__(inputs)
        self.terminal_exception: BaseException = terminal_exception if terminal_exception is not None else KeyboardInterrupt()

    def read_raw(self, prompt: str = "", /) -> str:
        """Return the next queued raw line or raise the configured terminal exception when exhausted."""

        self.prompts.append(prompt)

        if self.input_exception is not None:
            exc = self.input_exception
            self.input_exception = None
            raise exc

        if not self._inputs:
            raise self.terminal_exception

        line = self._inputs.pop(0)
        return line if line.endswith("\n") else f"{line}\n"


class StopAfterInputSource(testing.DummyInputSource):
    """Input source double that yields queued lines and immediately triggers a TaskEvent stop flag."""

    def __init__(self, stop_event: util.TaskEvent, lines: Sequence[str]) -> None:
        """Initialize with a cooperative stop event and test input lines."""

        super().__init__(lines)
        self._stop_event = stop_event

    def read_raw(self, prompt: str = "", /) -> str:
        """Yield the next queued input line and signal the cooperative stop event."""

        self.prompts.append(prompt)
        line = self._inputs.pop(0) if self._inputs else ""
        self._stop_event.set()
        return line


class ControlledStreamConnection(testing.DummyConnection):
    """Connection double capturing active timeout during read and signaling a cooperative stop event."""

    def __init__(
        self,
        client: contract.IOperationRenderer | None = None,
        incoming_chunks: Sequence[bytes] | None = None,
        initial_timeout: float | None = None,
        stop_event: util.TaskEvent | None = None,
    ) -> None:
        """Initialize connection double with timeout tracking and optional stop event."""

        super().__init__(client=client, incoming_chunks=incoming_chunks)
        self.timeout = initial_timeout
        self.observed_timeout_during_read: float | None = -1.0
        self._stop_event = stop_event

    def read(self) -> Generator[bytes, None, None]:
        """Record the active timeout setting and yield configured incoming byte chunks."""

        self.observed_timeout_during_read = self.timeout

        if self.read_error is not None:
            raise self.read_error

        yield from self.incoming_chunks

        if self._stop_event is not None:
            self._stop_event.set()


class TestLaunchShellDTO:
    """Tests verifying LaunchShellDTO defaults, customization, immutability, and equality."""

    def test_launch_shell_dto_init__default_banner__defaults_to_none(self) -> None:
        """LaunchShellDTO defaults banner to None when unspecified."""

        dto = LaunchShellDTO()

        assert dto.banner is None

    def test_launch_shell_dto_init__custom_banner__preserves_banner_string(self) -> None:
        """LaunchShellDTO preserves user-configured banner message."""

        banner = "=== Interactive Remote Shell ==="
        dto = LaunchShellDTO(banner=banner)

        assert dto.banner == banner

    def test_launch_shell_dto_immutability__reassign_attribute__raises_frozen_instance_error(self) -> None:
        """LaunchShellDTO is frozen and raises FrozenInstanceError on attribute mutation."""

        dto = LaunchShellDTO(banner="Initial Banner")

        with pytest.raises(FrozenInstanceError):
            dto.banner = "Modified Banner"  # type: ignore[misc]

    def test_launch_shell_dto_equality__identical_banners__evaluates_equal(self) -> None:
        """LaunchShellDTO instances with matching banner strings compare equal and share hash."""

        banner = "=== Interactive Remote Shell ==="
        dto_first = LaunchShellDTO(banner=banner)
        dto_second = LaunchShellDTO(banner=banner)

        assert dto_first == dto_second
        assert hash(dto_first) == hash(dto_second)


class TestLaunchShell:
    """Tests verifying LaunchShell task coordination, I/O handling, and lifecycle cleanup."""

    def test_launch_shell_init__stores_dto_and_initializes_stop_event_and_task_pool(self) -> None:
        """LaunchShell initializes and encapsulates its DTO, stop event, and bound task pool."""

        dto = LaunchShellDTO(banner="Interactive Session")
        command = LaunchShell(dto)

        assert command._dto is dto
        assert isinstance(command._stop_event, util.TaskEvent)
        assert not command._stop_event.is_set()
        assert isinstance(command._task_pool, util.TaskPool)
        assert command._task_pool._stop_event is command._stop_event

    def test_launch_shell_send_request__registers_and_starts_output_streamer_task(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
    ) -> None:
        """LaunchShell registers the output streamer task and starts the task pool."""

        dummy_connection.incoming_chunks = []
        dto = LaunchShellDTO()
        command = LaunchShell(dto)

        try:
            command.send_request(test_session)

            thread_names = [thread.name for thread in command._task_pool._threads]
            assert "shell_output_streamer" in thread_names
            assert any(thread.is_alive() for thread in command._task_pool._threads)
        finally:
            command._task_pool.stop()
            command._task_pool.wait_all()

    def test_launch_shell_read_response__missing_input_source__raises_invalid_operation(
        self,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """LaunchShell raises InvalidOperation when session context has no active input source."""

        session_without_input = contract.SessionContext(
            connection=dummy_connection,
            view=dummy_view,
            input_source=None,
            plugin_processor=dummy_file_store,
        )
        command = LaunchShell(LaunchShellDTO())

        with pytest.raises(config.InvalidOperation, match="Interactive shell requires an active input source."):
            command.read_response(session_without_input)

    def test_launch_shell_read_response__with_banner__writes_banner_message_to_view(
        self,
        test_session: contract.SessionContext,
        dummy_view: testing.DummyView,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """LaunchShell writes configured banner message to the view on initialization."""

        banner = "=== Interactive Remote Shell ==="
        dummy_input_source.input_exception = KeyboardInterrupt()
        dto = LaunchShellDTO(banner=banner)
        command = LaunchShell(dto)

        command.read_response(test_session)

        assert banner in dummy_view.messages
        assert "[keyboard interrupt received]" in dummy_view.messages

    def test_launch_shell_read_response__without_banner__does_not_write_banner_message(
        self,
        test_session: contract.SessionContext,
        dummy_view: testing.DummyView,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """LaunchShell omits banner message display when banner is None."""

        dummy_input_source.input_exception = KeyboardInterrupt()
        dto = LaunchShellDTO(banner=None)
        command = LaunchShell(dto)

        command.read_response(test_session)

        assert dummy_view.messages == ["[keyboard interrupt received]"]

    def test_launch_shell_read_response__keyboard_interrupt__writes_cancellation_message_and_suppresses_exception(
        self,
        test_session: contract.SessionContext,
        dummy_view: testing.DummyView,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """LaunchShell intercepts KeyboardInterrupt cleanly, notifies view, and exits without re-raising."""

        dummy_input_source.input_exception = KeyboardInterrupt()
        dto = LaunchShellDTO()
        command = LaunchShell(dto)

        command.read_response(test_session)

        assert "[keyboard interrupt received]" in dummy_view.messages

    def test_launch_shell_read_response__guarantees_task_pool_stop_and_wait_all_in_finally(
        self,
        test_session: contract.SessionContext,
        dummy_connection: testing.DummyConnection,
        dummy_input_source: testing.DummyInputSource,
    ) -> None:
        """LaunchShell ensures task pool stop and wait_all are invoked in finally block upon completion."""

        dummy_connection.incoming_chunks = []
        dummy_input_source.input_exception = KeyboardInterrupt()

        dto = LaunchShellDTO()
        command = LaunchShell(dto)

        command.send_request(test_session)
        assert not command._stop_event.is_set()

        command.read_response(test_session)

        assert command._stop_event.is_set()
        for thread in command._task_pool._threads:
            assert not thread.is_alive()

    def test_launch_shell_read_response__unexpected_exception__stops_task_pool_and_waits_in_finally(
        self,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
        dummy_file_store: testing.DummyPluginFileStore,
    ) -> None:
        """LaunchShell ensures task pool stop and wait_all run even when input handling raises an unhandled exception."""

        class CrashingInputSource(testing.DummyInputSource):
            def read_raw(self, prompt: str = "", /) -> str:
                raise RuntimeError("unexpected terminal crash")

        dummy_connection.incoming_chunks = []
        session = contract.SessionContext(
            connection=dummy_connection,
            view=dummy_view,
            input_source=CrashingInputSource(),
            plugin_processor=dummy_file_store,
        )
        command = LaunchShell(LaunchShellDTO())
        command.send_request(session)

        with pytest.raises(RuntimeError, match="unexpected terminal crash"):
            command.read_response(session)

        assert command._stop_event.is_set()
        for thread in command._task_pool._threads:
            assert not thread.is_alive()

    def test_launch_shell_input_handler__renders_commands_and_transmits_payload(
        self,
        dummy_connection: testing.DummyConnection,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """Shell input handler formats command through renderer and writes payload to connection."""

        stop_event = util.TaskEvent()
        input_command = "uname -a\n"
        rendered_command = "RENDERED_EXEC uname -a\n"
        dummy_profile.set_rendered_command(config.OperationCode.EXEC_COMMAND, rendered_command)

        input_source = StopAfterInputSource(stop_event, lines=[input_command])
        command = LaunchShell(LaunchShellDTO())
        handler = command._create_shell_input_handler(dummy_connection, input_source)

        handler(stop_event)

        assert dummy_profile.render_calls == [(config.OperationCode.EXEC_COMMAND, (input_command,))]
        assert dummy_connection.written == [rendered_command.encode("utf-8")]

    def test_launch_shell_input_handler__renderer_returns_none__falls_back_to_raw_command_bytes(
        self,
        dummy_connection: testing.DummyConnection,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """Shell input handler falls back to transmitting raw command bytes when renderer returns None."""

        stop_event = util.TaskEvent()
        input_command = "ps aux\n"
        dummy_profile.set_rendered_command(config.OperationCode.EXEC_COMMAND, None)

        input_source = StopAfterInputSource(stop_event, lines=[input_command])
        command = LaunchShell(LaunchShellDTO())
        handler = command._create_shell_input_handler(dummy_connection, input_source)

        handler(stop_event)

        assert dummy_profile.render_calls == [(config.OperationCode.EXEC_COMMAND, (input_command,))]
        assert dummy_connection.written == [input_command.encode("utf-8")]

    def test_launch_shell_input_handler__renderer_returns_empty_string__falls_back_to_raw_command_bytes(
        self,
        dummy_connection: testing.DummyConnection,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """Shell input handler falls back to transmitting raw command bytes when renderer returns an empty string."""

        stop_event = util.TaskEvent()
        input_command = "id\n"
        dummy_profile.set_rendered_command(config.OperationCode.EXEC_COMMAND, "")

        input_source = StopAfterInputSource(stop_event, lines=[input_command])
        command = LaunchShell(LaunchShellDTO())
        handler = command._create_shell_input_handler(dummy_connection, input_source)

        handler(stop_event)

        assert dummy_profile.render_calls == [(config.OperationCode.EXEC_COMMAND, (input_command,))]
        assert dummy_connection.written == [input_command.encode("utf-8")]

    def test_launch_shell_input_handler__empty_raw_input__skips_rendering_and_transmission(
        self,
        dummy_connection: testing.DummyConnection,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """Shell input handler gracefully skips rendering and transmission when read_raw returns an empty string."""

        stop_event = util.TaskEvent()
        input_source = StopAfterInputSource(stop_event, lines=[""])
        command = LaunchShell(LaunchShellDTO())
        handler = command._create_shell_input_handler(dummy_connection, input_source)

        handler(stop_event)

        assert dummy_profile.render_calls == []
        assert dummy_connection.written == []

    def test_launch_shell_output_handler__streams_chunks_and_restores_connection_timeout(
        self,
        dummy_view: testing.DummyView,
    ) -> None:
        """Shell output handler sets blocking timeout during read and restores configured timeout in finally."""

        stop_event = util.TaskEvent()
        initial_timeout = 25.5
        incoming_chunks = [b"stream_chunk_1\n", b"stream_chunk_2\n"]

        connection = ControlledStreamConnection(
            incoming_chunks=incoming_chunks,
            initial_timeout=initial_timeout,
            stop_event=stop_event,
        )
        command = LaunchShell(LaunchShellDTO())
        handler = command._create_shell_output_handler(connection, dummy_view)

        handler(stop_event)

        assert connection.observed_timeout_during_read is None
        assert connection.timeout == initial_timeout
        assert dummy_view.binary_data == incoming_chunks

    def test_launch_shell_output_handler__exception_during_read__restores_timeout_in_finally(
        self,
        dummy_view: testing.DummyView,
    ) -> None:
        """Shell output handler restores original connection timeout even when read raises an exception."""

        stop_event = util.TaskEvent()
        initial_timeout = 18.0
        connection = testing.DummyConnection()
        connection.timeout = initial_timeout
        connection.read_error = config.ConnectionError("socket read error")

        command = LaunchShell(LaunchShellDTO())
        handler = command._create_shell_output_handler(connection, dummy_view)

        with pytest.raises(config.ConnectionError, match="socket read error"):
            handler(stop_event)

        assert connection.timeout == initial_timeout

    def test_launch_shell_lifecycle__bidirectional_streaming_and_graceful_shutdown(
        self,
        dummy_connection: testing.DummyConnection,
        dummy_view: testing.DummyView,
        dummy_file_store: testing.DummyPluginFileStore,
        dummy_profile: testing.DummyConnectionProfile,
    ) -> None:
        """LaunchShell displays banner, forwards inputs, streams output, and terminates cleanly on interrupt."""

        banner = "=== Interactive Remote Shell ==="
        rendered_command = "RENDERED_EXEC id\n"
        initial_timeout = 12.5

        dummy_connection.timeout = initial_timeout
        dummy_connection.incoming_chunks = [b"uid=1000(dev) gid=1000(dev)\n"]
        dummy_profile.set_rendered_command(config.OperationCode.EXEC_COMMAND, rendered_command)

        input_source = ScriptedShellInputSource(["id\n"])
        session = contract.SessionContext(
            connection=dummy_connection,
            view=dummy_view,
            input_source=input_source,
            plugin_processor=dummy_file_store,
        )

        dto = LaunchShellDTO(banner=banner)
        command = LaunchShell(dto)

        command.send_request(session)
        command.read_response(session)

        assert banner in dummy_view.messages
        assert "[keyboard interrupt received]" in dummy_view.messages
        assert rendered_command.encode("utf-8") in dummy_connection.written
        assert dummy_connection.timeout == initial_timeout
        assert command._stop_event.is_set()
        for thread in command._task_pool._threads:
            assert not thread.is_alive()
