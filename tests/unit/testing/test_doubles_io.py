import pytest

from declusor import testing


class TestDummyView:
    """Verify behavior of the DummyView test double."""

    def test_write_and_capture_semantic_messages(self) -> None:
        """Ensure DummyView captures semantic message types in designated buffers."""

        view = testing.DummyView()
        err = ValueError("test error")

        view.write_message("standard message")
        view.write_error(err)
        view.write_warning("warning message")
        view.write_info("informational message")
        view.write_success("success message")
        view.write_binary_data(b"\x00\x01\x02\x03")

        assert view.messages == ["standard message"]
        assert view.errors == [err]
        assert view.warnings == ["warning message"]
        assert view.info_messages == ["informational message"]
        assert view.success_messages == ["success message"]
        assert view.binary_data == [b"\x00\x01\x02\x03"]

    def test_write_error_with_string_argument(self) -> None:
        """Ensure DummyView accepts string errors as well as Exception objects."""

        view = testing.DummyView()
        view.write_error("string formatted error")

        assert view.errors == ["string formatted error"]

    def test_reset_clears_all_captured_buffers(self) -> None:
        """Ensure reset() completely empties all recorded message buffers."""

        view = testing.DummyView()
        view.write_message("msg")
        view.write_error(RuntimeError("err"))
        view.write_warning("warn")
        view.write_info("info")
        view.write_success("ok")
        view.write_binary_data(b"data")

        view.reset()

        assert view.messages == []
        assert view.errors == []
        assert view.warnings == []
        assert view.info_messages == []
        assert view.success_messages == []
        assert view.binary_data == []


class TestDummyInputSource:
    """Verify behavior of the DummyInputSource test double."""

    def test_read_command_strips_whitespace_and_records_prompt(self) -> None:
        """Ensure read_command strips whitespace and logs the presented prompt."""

        input_source = testing.DummyInputSource(["  help  \n", "exit\t"])

        cmd1 = input_source.read_command("[declusor] > ")
        cmd2 = input_source.read_command("[declusor] > ")

        assert cmd1 == "help"
        assert cmd2 == "exit"
        assert input_source.prompts == ["[declusor] > ", "[declusor] > "]

    def test_read_raw_preserves_raw_formatting(self) -> None:
        """Ensure read_raw preserves trailing newlines and whitespace."""

        input_source = testing.DummyInputSource(["line 1\n", "  indented\n"])

        raw1 = input_source.read_raw("raw: ")
        raw2 = input_source.read_raw("raw: ")

        assert raw1 == "line 1\n"
        assert raw2 == "  indented\n"

    def test_exhausted_inputs_return_empty_defaults(self) -> None:
        """Ensure empty input queues return default empty values."""

        input_source = testing.DummyInputSource()

        assert input_source.read_command() == ""
        assert input_source.read_raw() == "\n"

    def test_feed_inputs_appends_to_active_queue(self) -> None:
        """Ensure feed_inputs enqueues additional commands dynamically."""

        input_source = testing.DummyInputSource()
        input_source.feed_inputs("first", "second")

        assert input_source.read_command() == "first"
        assert input_source.read_command() == "second"
        assert input_source.read_command() == ""

    def test_input_exception_raises_once_and_resets(self) -> None:
        """Ensure injected input_exception fires on read and resets automatically."""

        input_source = testing.DummyInputSource(["after_interrupt"])
        input_source.input_exception = KeyboardInterrupt("simulated cancel")

        with pytest.raises(KeyboardInterrupt, match="simulated cancel"):
            input_source.read_command()

        # Exception resets after firing
        assert input_source.input_exception is None
        assert input_source.read_command() == "after_interrupt"


class TestDummySocket:
    """Verify behavior of the DummySocket test double."""

    def test_initialization_and_metadata(self) -> None:
        """Ensure DummySocket initializes peer names, fileno, and timeouts."""

        sock = testing.DummySocket(
            incoming_bytes=b"sample payload",
            peer_name=("192.168.1.50", 4444),
            fileno_val=42,
            timeout=5.0,
        )

        assert sock.getpeername() == ("192.168.1.50", 4444)
        assert sock.fileno() == 42
        assert sock.gettimeout() == 5.0

    def test_send_and_sendall_record_data(self) -> None:
        """Ensure send and sendall record bytes and call histories."""

        sock = testing.DummySocket()

        sent_count = sock.send(b"ping")
        sock.sendall(b"-pong")

        assert sent_count == 4
        assert sock.sent_bytes == b"ping-pong"
        assert sock.send_calls == [b"ping"]
        assert sock.sendall_calls == [b"-pong"]

    def test_recv_from_incoming_byte_buffer(self) -> None:
        """Ensure recv reads from internal buffer and consumes bytes progressively."""

        sock = testing.DummySocket(incoming_bytes=b"abcdefghij")

        chunk1 = sock.recv(4)
        chunk2 = sock.recv(10)
        chunk3 = sock.recv(10)

        assert chunk1 == b"abcd"
        assert chunk2 == b"efghij"
        assert chunk3 == b""
        assert sock.recv_calls == [4, 10, 10]

    def test_feed_appends_to_incoming_stream(self) -> None:
        """Ensure feed adds new data to unread incoming stream."""

        sock = testing.DummySocket()
        sock.feed(b"stream1")
        sock.feed(b"stream2")

        assert sock.recv(20) == b"stream1stream2"

    def test_feed_recv_chunks_provides_discrete_frames(self) -> None:
        """Ensure feed_recv_chunks returns discrete chunks regardless of requested length."""

        sock = testing.DummySocket()
        sock.feed_recv_chunks(b"frame A", b"frame B")

        assert sock.recv(4096) == b"frame A"
        assert sock.recv(4096) == b"frame B"

    def test_settimeout_and_shutdown(self) -> None:
        """Ensure settimeout and shutdown update properties and call records."""

        sock = testing.DummySocket()

        sock.settimeout(12.5)
        assert sock.timeout == 12.5
        assert sock.settimeout_calls == [12.5]

        sock.shutdown(2)
        assert sock.shutdown_called is True
        assert sock.shutdown_calls == [2]

    def test_close_and_context_manager(self) -> None:
        """Ensure close() marks socket closed and context manager automatically cleans up."""

        sock = testing.DummySocket()
        assert not sock.closed

        with sock:
            assert not sock.closed
        assert sock.closed
        assert sock.close_calls == 1

        sock.close()
        assert sock.close_calls == 2

    def test_simulated_errors(self) -> None:
        """Ensure configured errors raise on corresponding socket operations."""

        sock = testing.DummySocket()

        sock.send_error = OSError("send failed")
        with pytest.raises(OSError, match="send failed"):
            sock.send(b"data")

        sock.sendall_error = BrokenPipeError("pipe broken")
        with pytest.raises(BrokenPipeError, match="pipe broken"):
            sock.sendall(b"data")

        sock.recv_error = TimeoutError("socket timed out")
        with pytest.raises(TimeoutError, match="socket timed out"):
            sock.recv(1024)

        sock.shutdown_error = OSError("shutdown failed")
        with pytest.raises(OSError, match="shutdown failed"):
            sock.shutdown(0)
