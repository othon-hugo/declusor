import pytest

from declusor import contract, testing


class PassthroughTransport(contract.ITransportLayer):
    """Minimal concrete ITransportLayer for testing delegation."""

    def read(self, max_bytes: int = 4096, /) -> bytes:
        """Forward read directly to the underlying transport."""

        return self._transport.read(max_bytes)

    def write(self, data: bytes, /) -> None:
        """Forward write directly to the underlying transport."""

        self._transport.write(data)


def test_transport_layer_delegates_is_closed() -> None:
    """ITransportLayer.is_closed must delegate to underlying transport."""

    inner = testing.DummyTransport()
    layer = PassthroughTransport(inner)

    assert not layer.is_closed
    inner.close()
    assert layer.is_closed


def test_transport_layer_delegates_timeout() -> None:
    """ITransportLayer.timeout must delegate get and set to underlying transport."""

    inner = testing.DummyTransport()
    layer = PassthroughTransport(inner)

    assert layer.timeout is None
    layer.timeout = 2.5
    assert layer.timeout == 2.5
    assert inner.timeout == 2.5


def test_transport_layer_delegates_peer_address() -> None:
    """ITransportLayer.peer_address must delegate to underlying transport."""

    inner = testing.DummyTransport(peer_address="10.0.0.1:8080")
    layer = PassthroughTransport(inner)

    assert layer.peer_address == "10.0.0.1:8080"


def test_transport_layer_delegates_close() -> None:
    """ITransportLayer.close must close the underlying transport."""

    inner = testing.DummyTransport()
    layer = PassthroughTransport(inner)

    layer.close()
    assert inner.is_closed
    assert layer.is_closed


def test_transport_layer_exposes_underlying() -> None:
    """ITransportLayer.underlying must return the wrapped transport."""

    inner = testing.DummyTransport()
    layer = PassthroughTransport(inner)

    assert layer.underlying is inner


def test_transport_layer_passthrough_read_write() -> None:
    """PassthroughTransport must transparently forward read and write."""

    inner = testing.DummyTransport(incoming_data=b"hello")
    layer = PassthroughTransport(inner)

    layer.write(b"outbound")
    assert inner.written_bytes == b"outbound"

    received = layer.read(4096)
    assert received == b"hello"


def test_transport_layer_context_manager() -> None:
    """ITransportLayer must support context manager protocol via ITransport."""

    inner = testing.DummyTransport()

    with PassthroughTransport(inner) as layer:
        assert not layer.is_closed

    assert inner.is_closed


def test_transport_layer_double_stacking() -> None:
    """Two stacked ITransportLayer instances must delegate correctly."""

    inner = testing.DummyTransport(incoming_data=b"deep")
    layer1 = PassthroughTransport(inner)
    layer2 = PassthroughTransport(layer1)

    layer2.write(b"stacked")
    assert inner.written_bytes == b"stacked"

    received = layer2.read(4096)
    assert received == b"deep"

    assert layer2.underlying is layer1
    assert layer1.underlying is inner


def test_transport_layer_is_abstract() -> None:
    """ITransportLayer cannot be instantiated directly."""

    inner = testing.DummyTransport()

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        contract.ITransportLayer(inner)  # type: ignore[abstract]
