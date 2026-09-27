import pytest

from declusor import config, testing


def test_dummy_transport_read_and_write_recording() -> None:
    """Verify DummyTransport replays configured data and records outgoing writes."""

    transport = testing.DummyTransport(incoming_data=b"hello from server")
    assert not transport.is_closed
    assert transport.peer_address == "127.0.0.1:54321"

    read_data = transport.read(4096)
    assert read_data == b"hello from server"

    transport.write(b"ack")
    assert transport.written_bytes == b"ack"
    assert transport.write_history == [b"ack"]

    transport.push_incoming(b"second message")
    assert transport.read(4096) == b"second message"


def test_dummy_transport_simulated_errors() -> None:
    """Verify DummyTransport can simulate read and write failures."""

    transport = testing.DummyTransport()

    transport.simulate_error_on_next_write(config.ConnectionError("Simulated write failure"))
    with pytest.raises(config.ConnectionError, match="Simulated write failure"):
        transport.write(b"fail")

    transport.simulate_error_on_next_read(config.ConnectionTimeoutError("Simulated read timeout"))
    with pytest.raises(config.ConnectionTimeoutError, match="Simulated read timeout"):
        transport.read()


def test_memory_transport_duplex_communication() -> None:
    """Verify bidirectional streaming across a MemoryTransport pair."""

    client, server = testing.create_memory_transport_pair()
    try:
        assert client.peer_address == "memory://server"
        assert server.peer_address == "memory://client"

        client.write(b"Ping from client")
        received_by_server = server.read(4096)
        assert received_by_server == b"Ping from client"

        server.write(b"Pong from server")
        received_by_client = client.read(4096)
        assert received_by_client == b"Pong from server"
    finally:
        client.close()
        server.close()


def test_memory_transport_fragmented_streaming() -> None:
    """Verify MemoryTransport supports multi-chunk streaming and read_exact."""

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


def test_memory_transport_eof_on_peer_close() -> None:
    """Verify closing one endpoint signals EOF (b'') to the other endpoint."""

    client, server = testing.create_memory_transport_pair()

    client.write(b"final")
    client.close()

    assert server.read(4096) == b"final"
    # Next read must return b"" indicating EOF
    assert server.read(4096) == b""

    # read_exact on EOF raises ConnectionClosed
    with pytest.raises(config.ConnectionClosed):
        server.read_exact(1)

    server.close()


def test_memory_transport_timeout() -> None:
    """Verify read raises ConnectionTimeoutError when timeout expires on empty buffer."""

    client, server = testing.create_memory_transport_pair()
    try:
        client.timeout = 0.05
        with pytest.raises(config.ConnectionTimeoutError):
            client.read(4096)
    finally:
        client.close()
        server.close()


def test_memory_transport_listener_accept_and_create_client() -> None:
    """Verify MemoryTransportListener enqueues and accepts in-memory transports."""

    listener = testing.MemoryTransportListener("memory://test-listener")
    try:
        assert listener.local_endpoint == "memory://test-listener"
        assert not listener.is_closed

        client = listener.create_client()
        server = listener.accept(timeout=1.0)
        try:
            client.write(b"Hello Server")
            assert server.read(4096) == b"Hello Server"

            server.write(b"Hello Client")
            assert client.read(4096) == b"Hello Client"
        finally:
            server.close()
            client.close()
    finally:
        listener.close()
        assert listener.is_closed


def test_memory_transport_listener_timeout() -> None:
    """Verify MemoryTransportListener.accept raises ConnectionTimeoutError on timeout."""

    listener = testing.MemoryTransportListener()
    try:
        with pytest.raises(config.ConnectionTimeoutError):
            listener.accept(timeout=0.05)
    finally:
        listener.close()


def test_memory_transport_listener_closed_accept_raises_error() -> None:
    """Verify accept on closed MemoryTransportListener raises ConnectionClosed."""

    listener = testing.MemoryTransportListener()
    listener.close()

    with pytest.raises(config.ConnectionClosed, match="Cannot accept on closed listener"):
        listener.accept()
