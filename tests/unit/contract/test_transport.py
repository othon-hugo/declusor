import pytest

from declusor import config, contract


class FakeTransport(contract.ITransport):
    """Minimal concrete implementation of ITransport for testing contract defaults."""

    def __init__(self, incoming_chunks: list[bytes] | None = None) -> None:
        self._chunks = list(incoming_chunks or [])
        self._written = bytearray()
        self._closed = False
        self._timeout: float | None = None

    @property
    def is_closed(self) -> bool:
        return self._closed

    @property
    def timeout(self) -> float | None:
        return self._timeout

    @timeout.setter
    def timeout(self, value: float | None, /) -> None:
        self._timeout = value

    @property
    def peer_address(self) -> str:
        return "127.0.0.1:54321"

    def read(self, max_bytes: int = 4096, /) -> bytes:
        if self._closed:
            raise config.ConnectionClosed("Transport is closed.")
        if not self._chunks:
            return b""
        chunk = self._chunks.pop(0)
        if len(chunk) <= max_bytes:
            return chunk
        self._chunks.insert(0, chunk[max_bytes:])
        return chunk[:max_bytes]

    def write(self, data: bytes, /) -> None:
        if self._closed:
            raise config.ConnectionClosed("Transport is closed.")
        self._written.extend(data)

    def close(self) -> None:
        self._closed = True


class FakeListener(contract.ITransportListener):
    """Minimal concrete implementation of ITransportListener."""

    def __init__(self) -> None:
        self._closed = False

    @property
    def local_endpoint(self) -> str:
        return "0.0.0.0:4444"

    def accept(self, timeout: float | None = None) -> contract.ITransport:
        if self._closed:
            raise config.ConnectionClosed("Listener is closed.")
        return FakeTransport()

    def close(self) -> None:
        self._closed = True


def test_transport_cannot_be_instantiated_directly() -> None:
    """Verify ITransport cannot be instantiated directly due to abstract methods."""

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        contract.ITransport()  # type: ignore[abstract]


def test_transport_listener_cannot_be_instantiated_directly() -> None:
    """Verify ITransportListener cannot be instantiated directly."""

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        contract.ITransportListener()  # type: ignore[abstract]


def test_transport_read_exact_zero_bytes() -> None:
    """Verify read_exact with 0 bytes immediately returns empty bytes."""

    transport = FakeTransport([b"some-data"])
    assert transport.read_exact(0) == b""


def test_transport_read_exact_negative_count_raises_value_error() -> None:
    """Verify read_exact with negative count raises ValueError."""

    transport = FakeTransport()
    with pytest.raises(ValueError, match="Count must be non-negative"):
        transport.read_exact(-1)


def test_transport_read_exact_single_chunk() -> None:
    """Verify read_exact returns full chunk when available in one read."""

    transport = FakeTransport([b"1234567890"])
    assert transport.read_exact(10) == b"1234567890"


def test_transport_read_exact_accumulates_fragmented_chunks() -> None:
    """Verify read_exact accumulates across multiple partial chunks."""

    transport = FakeTransport([b"123", b"456", b"7890"])
    assert transport.read_exact(10) == b"1234567890"


def test_transport_read_exact_preserves_leftover_in_stream() -> None:
    """Verify read_exact reads only the requested count and leaves remaining data."""

    transport = FakeTransport([b"ABCDEFGHIJ"])
    assert transport.read_exact(4) == b"ABCD"
    assert transport.read(6) == b"EFGHIJ"


def test_transport_read_exact_raises_connection_closed_on_early_eof() -> None:
    """Verify read_exact raises ConnectionClosed if stream ends before requested count."""

    transport = FakeTransport([b"123"])
    with pytest.raises(config.ConnectionClosed, match="expected 10 bytes, received 3"):
        transport.read_exact(10)


def test_transport_context_manager() -> None:
    """Verify context manager automatically closes the transport upon exit."""

    transport = FakeTransport()
    with transport as t:
        assert t is transport
        assert not t.is_closed
    assert transport.is_closed


def test_listener_context_manager() -> None:
    """Verify context manager automatically closes the listener upon exit."""

    listener = FakeListener()
    with listener as active_listener:
        assert active_listener is listener
        assert not listener._closed
    assert listener._closed
