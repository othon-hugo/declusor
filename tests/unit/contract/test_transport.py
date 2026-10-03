import pytest

from declusor import config, contract
from declusor.testing import DummyTransport, MemoryTransportListener

# [Test Cases]


class TestITransport:
    """Test suite for ITransport base contract and stream helpers."""

    def test_transport_direct_instantiation__raises_type_error(self) -> None:
        """Verify ITransport cannot be instantiated directly due to abstract methods."""

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            contract.ITransport()  # type: ignore[abstract]

    def test_transport_read_exact_zero_count__returns_empty_bytes(self) -> None:
        """Verify read_exact with count=0 immediately returns empty bytes without reading."""

        transport = DummyTransport(incoming_data=b"unconsumed_stream_data")

        result = transport.read_exact(0)

        assert result == b""

    def test_transport_read_exact_negative_count__raises_value_error(self) -> None:
        """Verify read_exact with negative count raises ValueError."""

        transport = DummyTransport()

        with pytest.raises(ValueError, match="Count must be non-negative, got -1."):
            transport.read_exact(-1)

    def test_transport_read_exact_single_chunk__returns_exact_bytes(self) -> None:
        """Verify read_exact returns full payload when satisfied in a single read."""

        transport = DummyTransport(incoming_data=b"hello world")

        result = transport.read_exact(11)

        assert result == b"hello world"

    def test_transport_read_exact_fragmented_chunks__accumulates_into_exact_bytes(self) -> None:
        """Verify read_exact accumulates across multiple fragmented stream chunks."""

        transport = DummyTransport(incoming_data=[b"chunk_", b"by_", b"chunk"])

        result = transport.read_exact(14)

        assert result == b"chunk_by_chunk"

    def test_transport_read_exact_excess_stream_data__preserves_unread_bytes(self) -> None:
        """Verify read_exact reads only the requested count and leaves remaining stream data."""

        transport = DummyTransport(incoming_data=b"ABCDEFGHIJ")

        first_chunk = transport.read_exact(4)
        remaining_chunk = transport.read(6)

        assert first_chunk == b"ABCD"
        assert remaining_chunk == b"EFGHIJ"

    def test_transport_read_exact_premature_eof__raises_connection_closed(self) -> None:
        """Verify read_exact raises ConnectionClosed if EOF occurs before count bytes are read."""

        transport = DummyTransport(incoming_data=b"short")

        with pytest.raises(config.ConnectionClosed, match="Transport closed prematurely: expected 10 bytes, received 5."):
            transport.read_exact(10)

    def test_transport_context_manager_scope__returns_self_and_closes_on_exit(self) -> None:
        """Verify context manager protocol returns self and closes transport upon exit."""

        transport = DummyTransport()

        with transport as active_transport:
            assert active_transport is transport
            assert active_transport.is_closed is False

        assert transport.is_closed is True

    def test_transport_context_manager_scope__exception_raised__closes_on_exit(self) -> None:
        """Verify context manager protocol guarantees invoking close even when exception is raised."""

        transport = DummyTransport()

        with pytest.raises(RuntimeError, match="stream failure"):
            with transport:
                raise RuntimeError("stream failure")

        assert transport.is_closed is True

    def test_transport_read_exact__keyword_argument__raises_type_error(self) -> None:
        """Verify read_exact enforces positional-only argument passing."""

        transport = DummyTransport()

        with pytest.raises(TypeError, match="positional-only"):
            transport.read_exact(count=5)  # type: ignore[call-arg]


class TestITransportListener:
    """Test suite for ITransportListener base contract and lifecycle."""

    def test_transport_listener_direct_instantiation__raises_type_error(self) -> None:
        """Verify ITransportListener cannot be instantiated directly due to abstract methods."""

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            contract.ITransportListener()  # type: ignore[abstract]

    def test_transport_listener_context_manager_scope__returns_self_and_closes_on_exit(self) -> None:
        """Verify context manager protocol returns self and closes listener upon exit."""

        listener = MemoryTransportListener(endpoint="memory://listener")

        with listener as active_listener:
            assert active_listener is listener
            assert active_listener.is_closed is False

        assert listener.is_closed is True

    def test_transport_listener_context_manager_scope__exception_raised__closes_on_exit(self) -> None:
        """Verify listener context manager guarantees close even when exception is raised."""

        listener = MemoryTransportListener(endpoint="memory://listener")

        with pytest.raises(RuntimeError, match="listener failure"):
            with listener:
                raise RuntimeError("listener failure")

        assert listener.is_closed is True
