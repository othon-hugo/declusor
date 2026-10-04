import pytest

from declusor import config, contract, testing


class TestDummyConnectionLifecycle:
    """Verify state transitions and lifecycle methods of DummyConnection."""

    def test_initial_state_and_handshake(self) -> None:
        """Ensure initial state is CREATED and handshake transitions to CONNECTED."""

        conn = testing.DummyConnection(initial_state=contract.ConnectionState.CREATED)

        initial_state: contract.ConnectionState = conn.state
        assert initial_state == contract.ConnectionState.CREATED
        assert not conn.initialize_called

        conn.handshake()

        post_state: contract.ConnectionState = conn.state
        assert post_state == contract.ConnectionState.CONNECTED
        assert conn.initialize_called

    def test_handshake_when_already_connected_raises_error(self) -> None:
        """Ensure handshake() raises ConnectionError when connection is already connected."""

        conn = testing.DummyConnection(initial_state=contract.ConnectionState.CONNECTED)

        with pytest.raises(config.ConnectionError, match="Connection is already initialized"):
            conn.handshake()

    def test_close_transitions_to_closed(self) -> None:
        """Ensure close() transitions state to CLOSED and marks closed flag."""

        conn = testing.DummyConnection()
        assert not conn.closed

        conn.close()

        assert conn.closed
        assert conn.state == contract.ConnectionState.CLOSED

    def test_context_manager_lifecycle(self) -> None:
        """Ensure context manager cleanly closes connection on exit."""

        conn = testing.DummyConnection()

        with conn:
            assert not conn.closed
        assert conn.closed
        assert conn.state == contract.ConnectionState.CLOSED


class TestDummyConnectionIO:
    """Verify read, write, and parameter operations of DummyConnection."""

    def test_write_records_payloads(self) -> None:
        """Ensure write records transmitted byte chunks."""

        conn = testing.DummyConnection(initial_state=contract.ConnectionState.CONNECTED)
        conn.write(b"payload 1")
        conn.write(b"payload 2")

        assert conn.written == [b"payload 1", b"payload 2"]

    def test_read_streams_configured_chunks(self) -> None:
        """Ensure read streams default or custom chunk sequences."""

        conn = testing.DummyConnection(initial_state=contract.ConnectionState.CONNECTED)
        chunks = list(conn.read())

        assert chunks == [b"chunk1\n", b"chunk2\n"]

    def test_timeout_property(self) -> None:
        """Ensure timeout can be read and mutated."""

        conn = testing.DummyConnection()
        assert conn.timeout is None

        conn.timeout = 7.5
        assert conn.timeout == 7.5


class TestDummyConnectionErrors:
    """Verify error injection and closed-state guards in DummyConnection."""

    def test_initialize_error_raises_on_handshake(self) -> None:
        """Ensure configured initialize_error fires on handshake()."""

        conn = testing.DummyConnection(initial_state=contract.ConnectionState.CREATED)
        conn.initialize_error = config.ConnectionHandshakeError("handshake failed")

        with pytest.raises(config.ConnectionHandshakeError, match="handshake failed"):
            conn.handshake()

    def test_unconnected_connection_rejects_read_and_write(self) -> None:
        """Ensure CREATED connection refuses read and write operations."""

        conn = testing.DummyConnection(initial_state=contract.ConnectionState.CREATED)

        with pytest.raises(config.ConnectionError, match="Cannot perform I/O on connection that is not connected"):
            conn.write(b"data")

        with pytest.raises(config.ConnectionError, match="Cannot perform I/O on connection that is not connected"):
            list(conn.read())

    def test_write_error_raises_on_write(self) -> None:
        """Ensure configured write_error fires on write()."""

        conn = testing.DummyConnection(initial_state=contract.ConnectionState.CONNECTED)
        conn.write_error = config.ConnectionError("network write failed")

        with pytest.raises(config.ConnectionError, match="network write failed"):
            conn.write(b"data")

    def test_read_error_raises_on_read(self) -> None:
        """Ensure configured read_error fires when iterating read()."""

        conn = testing.DummyConnection(initial_state=contract.ConnectionState.CONNECTED)
        conn.read_error = config.ConnectionTimeoutError("read timeout")

        with pytest.raises(config.ConnectionTimeoutError, match="read timeout"):
            list(conn.read())

    def test_closed_connection_rejects_handshake_and_write(self) -> None:
        """Ensure closed connection refuses initialization and write operations."""

        conn = testing.DummyConnection()
        conn.close()

        with pytest.raises(config.ConnectionError, match="Cannot initialize a closed connection"):
            conn.handshake()

        with pytest.raises(config.ConnectionClosed, match="Connection is not open"):
            conn.write(b"data")


class TestDummyOperationRenderer:
    """Verify operation rendering and call tracking in DummyOperationRenderer."""

    def test_default_rendered_command_formatting(self) -> None:
        """Ensure default rendering joins opcode and arguments with spaces."""

        renderer = testing.DummyOperationRenderer(name="test_renderer")

        rendered = renderer.render_operation_command(config.OperationCode.EXEC_FILE, "script.sh", "arg1")
        assert rendered == f"{config.OperationCode.EXEC_FILE.value} script.sh arg1"
        assert renderer.render_calls == [(config.OperationCode.EXEC_FILE, ("script.sh", "arg1"))]

    def test_custom_rendered_command_override(self) -> None:
        """Ensure set_rendered_command overrides the rendered output for specific opcodes."""

        renderer = testing.DummyOperationRenderer()
        renderer.set_rendered_command(config.OperationCode.LOAD_MODULE, "custom_module_payload")

        result = renderer.render_operation_command(config.OperationCode.LOAD_MODULE, "mod.py")
        assert result == "custom_module_payload"

    def test_connection_profile_alias_compatibility(self) -> None:
        """Ensure DummyConnectionProfile alias inherits from DummyOperationRenderer."""

        profile = testing.DummyConnectionProfile()
        assert isinstance(profile, testing.DummyOperationRenderer)
