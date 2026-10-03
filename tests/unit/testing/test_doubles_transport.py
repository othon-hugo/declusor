import pytest

from declusor import config, testing


class TestDummyTransport:
    """Verify behavior of the DummyTransport double."""

    def test_read_and_write_recording(self) -> None:
        """Ensure DummyTransport replays incoming data and records outgoing writes."""

        transport = testing.DummyTransport(incoming_data=b"hello from server")
        assert not transport.is_closed
        assert transport.peer_address == "127.0.0.1:54321"

        read_data = transport.read(4096)
        assert read_data == b"hello from server"

        transport.write(b"ack")
        assert transport.written_bytes == b"ack"
        assert transport.write_history == [b"ack"]

    def test_push_incoming_data_dynamically(self) -> None:
        """Ensure push_incoming enqueues additional bytes for subsequent reads."""

        transport = testing.DummyTransport()
        transport.push_incoming(b"chunk1")
        transport.push_incoming(b"chunk2")

        assert transport.read(6) == b"chunk1"
        assert transport.read(6) == b"chunk2"

    def test_simulated_errors(self) -> None:
        """Ensure simulated read and write errors fire on the next invocation."""

        transport = testing.DummyTransport()

        transport.simulate_error_on_next_write(config.ConnectionError("Simulated write failure"))
        with pytest.raises(config.ConnectionError, match="Simulated write failure"):
            transport.write(b"fail")

        transport.simulate_error_on_next_read(config.ConnectionTimeoutError("Simulated read timeout"))
        with pytest.raises(config.ConnectionTimeoutError, match="Simulated read timeout"):
            transport.read()

    def test_close_and_lifecycle(self) -> None:
        """Ensure close() marks transport closed and rejects operations."""

        transport = testing.DummyTransport()
        transport.close()

        assert transport.is_closed

        with pytest.raises(config.ConnectionClosed):
            transport.write(b"data")


class TestMemoryTransport:
    """Verify in-memory bidirectional duplex transport communication."""

    def test_duplex_communication(self) -> None:
        """Ensure client and server endpoints communicate bidirectionally in memory."""

        client, server = testing.create_memory_transport_pair()
        try:
            assert client.peer_address == "memory://server"
            assert server.peer_address == "memory://client"

            client.write(b"ping from client")
            received_server = server.read(4096)
            assert received_server == b"ping from client"

            server.write(b"pong from server")
            received_client = client.read(4096)
            assert received_client == b"pong from server"
        finally:
            client.close()
            server.close()

    def test_fragmented_streaming_and_read_exact(self) -> None:
        """Ensure multi-chunk stream delivery satisfies read_exact."""

        client, server = testing.create_memory_transport_pair()
        try:
            client.write(b"Part1-")
            client.write(b"Part2-")
            client.write(b"Part3")

            exact = server.read_exact(17)
            assert exact == b"Part1-Part2-Part3"
        finally:
            client.close()
            server.close()

    def test_eof_on_peer_close(self) -> None:
        """Ensure closing one endpoint signals EOF (b'') to the other endpoint."""

        client, server = testing.create_memory_transport_pair()

        client.write(b"final data")
        client.close()

        assert server.read(4096) == b"final data"
        assert server.read(4096) == b""

        with pytest.raises(config.ConnectionClosed):
            server.read_exact(1)

        server.close()

    def test_read_timeout_on_empty_buffer(self) -> None:
        """Ensure read raises ConnectionTimeoutError when timeout expires on empty buffer."""

        client, server = testing.create_memory_transport_pair()
        try:
            client.timeout = 0.05
            with pytest.raises(config.ConnectionTimeoutError):
                client.read(4096)
        finally:
            client.close()
            server.close()

    def test_write_on_closed_transport_raises(self) -> None:
        """Ensure writing to a closed transport raises ConnectionClosed."""

        client, server = testing.create_memory_transport_pair()
        client.close()
        server.close()

        with pytest.raises(config.ConnectionClosed):
            client.write(b"data")


class TestMemoryTransportListener:
    """Verify accept flow and lifecycle of MemoryTransportListener."""

    def test_enqueue_and_accept_pairing(self) -> None:
        """Ensure create_client creates a paired transport accepted by listener."""

        listener = testing.MemoryTransportListener("memory://custom-endpoint")
        try:
            assert listener.local_endpoint == "memory://custom-endpoint"
            assert not listener.is_closed

            client = listener.create_client()
            server = listener.accept(timeout=1.0)
            try:
                client.write(b"client hello")
                assert server.read(4096) == b"client hello"

                server.write(b"server reply")
                assert client.read(4096) == b"server reply"
            finally:
                client.close()
                server.close()
        finally:
            listener.close()
            assert listener.is_closed

    def test_accept_timeout_on_empty_queue(self) -> None:
        """Ensure accept raises ConnectionTimeoutError when timeout expires with no clients."""

        listener = testing.MemoryTransportListener()
        try:
            with pytest.raises(config.ConnectionTimeoutError):
                listener.accept(timeout=0.05)
        finally:
            listener.close()

    def test_accept_on_closed_listener_raises_connection_closed(self) -> None:
        """Ensure accept on closed listener raises ConnectionClosed."""

        listener = testing.MemoryTransportListener()
        listener.close()

        with pytest.raises(config.ConnectionClosed, match="Cannot accept on closed listener"):
            listener.accept()

    def test_close_idempotency(self) -> None:
        """Ensure close() can be called repeatedly without raising."""

        listener = testing.MemoryTransportListener()
        listener.close()
        listener.close()

        assert listener.is_closed
