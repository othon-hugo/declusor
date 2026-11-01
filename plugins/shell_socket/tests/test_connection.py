"""Unit tests verifying ShellSocketConnection nonce-delimited streaming and handshake."""

import threading
import time
from collections.abc import Callable
from pathlib import Path

import declusor_shell_socket as shell_socket
import pytest

from declusor import config, contract, testing


class TestShellSocketConnectionLifecycle:
    """Tests for ShellSocketConnection lifecycle transitions, handshake, and configuration."""

    def test_connection_state__transitions_through_lifecycle(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify connection lifecycle transitions: CREATED -> CONNECTED -> CLOSED."""

        trans = testing.DummyTransport(incoming_data=b"__DECLUSOR_EOF_test_nonce__\n")
        conn, _ = make_shell_connection(trans)

        initial_state: contract.ConnectionState = conn.state
        assert initial_state == contract.ConnectionState.CREATED

        conn.handshake()
        connected_state: contract.ConnectionState = conn.state
        assert connected_state == contract.ConnectionState.CONNECTED

        conn.close()
        closed_state: contract.ConnectionState = conn.state
        assert closed_state == contract.ConnectionState.CLOSED

        # Calling close again must be idempotent
        conn.close()
        reclosed_state: contract.ConnectionState = conn.state
        assert reclosed_state == contract.ConnectionState.CLOSED

    def test_handshake__when_already_connected__raises_connection_error(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify handshake raises ConnectionError when connection is already connected."""

        conn, trans = make_shell_connection(default_nonce="fixed_handshake_nonce")
        trans.push_incoming(b"__DECLUSOR_EOF_fixed_handshake_nonce__\n")
        conn.handshake()

        with pytest.raises(config.ConnectionError, match="Connection is already initialized"):
            conn.handshake()

    def test_handshake__when_connection_is_closed__raises_connection_error(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify handshake raises ConnectionError when connection is already closed."""

        conn, _ = make_shell_connection()
        conn.close()

        with pytest.raises(config.ConnectionError, match="Cannot initialize a closed connection"):
            conn.handshake()

    def test_handshake__when_transport_fails__raises_connection_handshake_error(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify handshake raises ConnectionHandshakeError when reading handshake envelope fails."""

        trans = testing.DummyTransport()
        trans.simulate_error_on_next_read(config.ConnectionTimeoutError("handshake timeout"))
        conn, _ = make_shell_connection(trans)

        with pytest.raises(config.ConnectionHandshakeError, match="Failed waiting for client handshake envelope"):
            conn.handshake()

    def test_handshake__transport_establishment_failure__closes_connection(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Close the connection when a transport layer cannot establish its session."""

        conn, trans = make_shell_connection()

        def establish() -> None:
            raise config.ConnectionError("transport negotiation failed")

        trans.establish = establish  # type: ignore[method-assign]

        with pytest.raises(config.ConnectionHandshakeError, match="Failed establishing transport session"):
            conn.handshake()

        assert conn.is_closed
        assert trans.is_closed

    def test_handshake__with_ephemeral_envelope__sends_helpers_and_transitions(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify handshake sends helpers and waits for dynamic envelope."""

        conn, trans = make_shell_connection(
            default_nonce="fixed_handshake_nonce",
        )
        trans.push_incoming(b"__DECLUSOR_EOF_fixed_handshake_nonce__\n")
        conn.handshake()

        assert conn.state == contract.ConnectionState.CONNECTED
        assert trans.written_bytes.startswith(b"fixed_handshake_nonce\x00")

    def test_handshake__staged_payload_present__transmits_nul_terminated_stage1_before_handshake(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify ShellSocketConnection transmits NUL-terminated Stage 1 payload when staged."""

        stage1 = b"echo 'staged payload'"
        conn, trans = make_shell_connection(
            default_nonce="fixed_handshake_nonce",
            stage1_payload=stage1,
        )
        trans.push_incoming(b"__DECLUSOR_EOF_fixed_handshake_nonce__\n")
        conn.handshake()

        assert conn.state == contract.ConnectionState.CONNECTED
        assert trans.written_bytes.startswith(stage1 + b"\x00")

    def test_handshake__with_segmented_envelope__accumulates_chunks_properly(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify handshake envelope handles segmented byte streaming properly."""

        trans = testing.DummyTransport(
            incoming_data=[
                b"__DECLUSOR_EOF_",
                b"test_",
                b"nonce__\n",
            ]
        )
        conn, _ = make_shell_connection(trans)
        conn.handshake()

        assert conn.state == contract.ConnectionState.CONNECTED

    def test_init__with_invalid_buffer_size__raises_connection_error(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify ShellSocketConnection raises ConnectionError when buffer_size <= 0."""

        with pytest.raises(config.ConnectionError, match="buffer_size must be > 0"):
            make_shell_connection(buffer_size=0)

        with pytest.raises(config.ConnectionError, match="buffer_size must be > 0"):
            make_shell_connection(buffer_size=-1)

    def test_properties__renderer_and_timeout__delegate_correctly(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify renderer and timeout property accessors."""

        conn, trans = make_shell_connection(timeout=2.5)
        assert conn.renderer is not None
        assert conn.timeout == 2.5
        assert trans.timeout == 2.5

        conn.timeout = 5.0
        assert conn.timeout == 5.0
        assert trans.timeout == 5.0

    def test_write__with_nonce_factory__generates_sequential_nonces(
        self,
        tmp_path: Path,
    ) -> None:
        """Verify ShellSocketConnection utilizes nonce_factory when fixed_nonce is None."""

        launchers = tmp_path / "launchers"
        launchers.mkdir(exist_ok=True)
        launcher = launchers / "shell_socket_client.sh"
        launcher.write_text("$HOST:$PORT", encoding="utf-8")
        (tmp_path / "helpers").mkdir(exist_ok=True)
        (tmp_path / "modules").mkdir(exist_ok=True)

        trans = testing.DummyTransport(peer_address="127.0.0.1:9000")
        renderer = shell_socket.ShellSocketRenderer()
        fs = contract.PluginFilesystem.from_root(tmp_path)
        files = shell_socket.ShellSocketProcessor(fs)

        counter = 0

        def mock_nonce() -> str:
            nonlocal counter
            counter += 1
            return f"generated_nonce_{counter}"

        conn = shell_socket.ShellSocketConnection(
            trans,
            renderer,
            files,
            fixed_nonce=None,
            nonce_factory=mock_nonce,
        )
        conn._state = contract.ConnectionState.CONNECTED

        conn.write(b"data1")
        assert trans.written_bytes == b"generated_nonce_1\x00data1\x00"
        assert conn.current_nonce == "generated_nonce_1"

        conn.write(b"data2")
        assert trans.written_bytes == b"generated_nonce_1\x00data1\x00generated_nonce_2\x00data2\x00"
        assert conn.current_nonce == "generated_nonce_2"


class TestShellSocketConnectionIO:
    """Tests for ShellSocketConnection command transmission and response reading."""

    def test_write__uses_ephemeral_envelope_framing(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify write transmits ephemeral nonce prefix followed by null-delimited payload."""

        connection, trans = make_shell_connection(default_nonce="fixed_nonce", connected=True)

        connection.write(b"command")
        assert trans.written_bytes == b"fixed_nonce\x00command\x00"

    def test_write__when_connection_is_created__raises_connection_error(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify write on CREATED connection raises ConnectionError before handshake."""

        conn, _ = make_shell_connection(connected=False)

        with pytest.raises(config.ConnectionError, match="Cannot perform I/O on connection that is not connected"):
            conn.write(b"command")

    def test_write__when_connection_is_closed__raises_connection_closed(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify write on closed connection raises ConnectionClosed."""

        conn, _ = make_shell_connection()
        conn.close()

        with pytest.raises(config.ConnectionClosed, match="Connection is closed"):
            conn.write(b"command")

    def test_write__when_transport_fails__translates_to_connection_error(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify write translates transport errors into domain ConnectionError."""

        trans = testing.DummyTransport()
        trans.simulate_error_on_next_write(config.ConnectionError("transport write failed"))
        connection, _ = make_shell_connection(trans, connected=True)

        with pytest.raises(config.ConnectionError, match="Failed to write to connection"):
            connection.write(b"command")

        assert len(connection._nonce_queue) == 0
        assert not connection._nonce_ready.is_set()

    def test_read__when_connection_is_created__raises_connection_error(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify read on CREATED connection raises ConnectionError before handshake."""

        conn, _ = make_shell_connection(connected=False)

        with pytest.raises(config.ConnectionError, match="Cannot perform I/O on connection that is not connected"):
            list(conn.read())

    def test_read__when_connection_is_closed__raises_connection_closed(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify read on closed connection raises ConnectionClosed."""

        conn, _ = make_shell_connection()
        conn.close()

        with pytest.raises(config.ConnectionClosed, match="Connection is closed"):
            list(conn.read())

    def test_read__when_nonce_is_missing__returns_empty_cleanly(
        self,
        tmp_path: Path,
    ) -> None:
        """Verify read returns empty generator cleanly when no active command nonce exists."""

        launchers = tmp_path / "launchers"
        launchers.mkdir(exist_ok=True)
        (launchers / "shell_socket_client.sh").write_text("$HOST:$PORT", encoding="utf-8")
        (tmp_path / "helpers").mkdir(exist_ok=True)
        (tmp_path / "modules").mkdir(exist_ok=True)

        trans = testing.DummyTransport(peer_address="127.0.0.1:9000")
        renderer = shell_socket.ShellSocketRenderer()
        fs = contract.PluginFilesystem.from_root(tmp_path)
        files = shell_socket.ShellSocketProcessor(fs)

        conn = shell_socket.ShellSocketConnection(
            trans,
            renderer,
            files,
            fixed_nonce=None,
        )
        conn._state = contract.ConnectionState.CONNECTED

        assert list(conn.read()) == []

    def test_read__with_ephemeral_envelope__terminates_at_delimiter(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify write transmits ephemeral nonce prefix and read terminates at dynamic envelope."""

        conn, trans = make_shell_connection(connected=True)
        conn.write(b"ls -la", nonce="abcdef0123456789")

        assert trans.written_bytes == b"abcdef0123456789\x00ls -la\x00"
        assert conn.current_nonce == "abcdef0123456789"

        envelope = b"__DECLUSOR_EOF_abcdef0123456789__\n"
        trans.push_incoming(b"output_chunk_1\n" + b"output_chunk_2\n" + envelope)

        chunks = list(conn.read())
        assert chunks == [b"output_chunk_1\noutput_chunk_2\n"]

    def test_read__when_delimiter_is_split_across_chunks__yields_payload_cleanly(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify read yields command output and terminates when envelope delimiter is split across reads."""

        conn, trans = make_shell_connection(connected=True)
        conn.write(b"id", nonce="split_test_nonce")

        delim = b"__DECLUSOR_EOF_split_test_nonce__\n"
        # Split delimiter across two chunks: chunk 1 has part of payload + first part of delim, chunk 2 has rest of delim
        split_idx = len(delim) // 2
        chunk1 = b"uid=0(root) gid=0(root)\n" + delim[:split_idx]
        chunk2 = delim[split_idx:]
        trans.push_incoming(chunk1)
        trans.push_incoming(chunk2)

        chunks = list(conn.read())
        assert b"".join(chunks) == b"uid=0(root) gid=0(root)\n"

    def test_read__when_write_occurs_while_waiting__unblocks_and_yields_output(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify read unblocks and consumes output when write occurs on another thread while waiting."""

        conn, trans = make_shell_connection(connected=True)

        def delayed_write() -> None:
            time.sleep(0.02)
            trans.push_incoming(b"async_output\n__DECLUSOR_EOF_delayed_nonce__\n")
            conn.write(b"delayed_cmd", nonce="delayed_nonce")

        writer_thread = threading.Thread(target=delayed_write)
        writer_thread.start()

        chunks = list(conn.read())
        writer_thread.join()

        assert chunks == [b"async_output\n"]

    def test_read__when_closed_while_waiting__raises_connection_closed(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify read unblocks immediately and raises ConnectionClosed when connection is closed while waiting."""

        conn, _ = make_shell_connection(connected=True)

        def delayed_close() -> None:
            time.sleep(0.02)
            conn.close()

        closer_thread = threading.Thread(target=delayed_close)
        closer_thread.start()

        with pytest.raises(config.ConnectionClosed, match="Connection is closed"):
            list(conn.read())

        closer_thread.join()

    def test_read__when_multiple_commands_pipelined__processes_sequential_envelopes(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify sequential pipelined writes and reads process each transaction envelope in order."""

        conn, trans = make_shell_connection(connected=True)

        conn.write(b"cmd1", nonce="nonce1")
        conn.write(b"cmd2", nonce="nonce2")

        trans.push_incoming(b"output1\n__DECLUSOR_EOF_nonce1__\noutput2\n__DECLUSOR_EOF_nonce2__\n")

        chunks1 = list(conn.read())
        assert chunks1 == [b"output1\n"]
        assert conn.current_nonce == "nonce2"

        chunks2 = list(conn.read())
        assert chunks2 == [b"output2\n"]
        assert conn.current_nonce is None

    def test_read__when_transport_times_out__raises_connection_timeout_error(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify read raises ConnectionTimeoutError when transport read times out."""

        trans = testing.DummyTransport()
        conn, _ = make_shell_connection(trans, connected=True)
        conn.write(b"cmd", nonce="timeout_nonce")

        trans.simulate_error_on_next_read(config.ConnectionTimeoutError("socket timeout"))

        with pytest.raises(config.ConnectionTimeoutError, match="socket timeout"):
            list(conn.read())

    def test_read__when_client_closes_stream_unexpectedly__raises_connection_closed(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify read raises ConnectionClosed when remote peer closes during stream."""

        trans = testing.DummyTransport()
        conn, _ = make_shell_connection(trans, connected=True)
        conn.write(b"cmd", nonce="closed_nonce")

        with pytest.raises(config.ConnectionClosed, match="Connection closed by client during response stream"):
            list(conn.read())

    def test_read__when_transport_error_during_read__translates_to_connection_closed(
        self,
        make_shell_connection: Callable[..., tuple[shell_socket.ShellSocketConnection, testing.DummyTransport]],
    ) -> None:
        """Verify read translates generic transport errors to ConnectionClosed."""

        trans = testing.DummyTransport()
        conn, _ = make_shell_connection(trans, connected=True)
        conn.write(b"cmd", nonce="error_nonce")

        trans.simulate_error_on_next_read(config.ConnectionError("network reset"))

        with pytest.raises(config.ConnectionClosed, match="Connection interrupted during read"):
            list(conn.read())
