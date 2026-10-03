import pytest

from declusor import contract
from declusor.testing import DummyTransport

# [Test Doubles]


class ConcreteTransportLayer(contract.ITransportLayer):
    """Minimal concrete implementation of ITransportLayer forwarding read and write."""

    def read(self, max_bytes: int = 4096, /) -> bytes:
        """Forward read operation directly to underlying transport."""

        return self._transport.read(max_bytes)

    def write(self, data: bytes, /) -> None:
        """Forward write operation directly to underlying transport."""

        self._transport.write(data)


# [Test Cases]


class TestITransportLayer:
    """Test suite for ITransportLayer base decorator contract."""

    def test_transport_layer_inheritance__inherits_from_itransport(self) -> None:
        """Verify ITransportLayer subclasses ITransport base contract."""

        assert issubclass(contract.ITransportLayer, contract.ITransport)

    def test_transport_layer_direct_instantiation__raises_type_error(self) -> None:
        """Verify ITransportLayer cannot be instantiated directly due to abstract read and write."""

        inner = DummyTransport()

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            contract.ITransportLayer(inner)  # type: ignore[abstract]

    def test_transport_layer_underlying_property__returns_wrapped_transport(self) -> None:
        """Verify underlying property returns the wrapped transport instance."""

        inner = DummyTransport()
        layer = ConcreteTransportLayer(inner)

        assert layer.underlying is inner

    def test_transport_layer_is_closed__delegates_to_underlying_transport(self) -> None:
        """Verify is_closed property delegates directly to underlying transport."""

        inner = DummyTransport()
        layer = ConcreteTransportLayer(inner)

        assert layer.is_closed is False

        inner.close()

        assert layer.is_closed is True

    def test_transport_layer_timeout_getter__delegates_to_underlying_transport(self) -> None:
        """Verify timeout getter delegates directly to underlying transport."""

        inner = DummyTransport()
        layer = ConcreteTransportLayer(inner)

        assert layer.timeout is None

        inner.timeout = 2.5

        assert layer.timeout == 2.5

    def test_transport_layer_timeout_setter__delegates_to_underlying_transport(self) -> None:
        """Verify timeout setter mutates timeout on underlying transport."""

        inner = DummyTransport()
        layer = ConcreteTransportLayer(inner)

        layer.timeout = 4.0

        assert inner.timeout == 4.0
        assert layer.timeout == 4.0

    def test_transport_layer_peer_address__delegates_to_underlying_transport(self) -> None:
        """Verify peer_address property delegates directly to underlying transport."""

        inner = DummyTransport(peer_address="192.168.1.100:9999")
        layer = ConcreteTransportLayer(inner)

        assert layer.peer_address == "192.168.1.100:9999"

    def test_transport_layer_close__delegates_to_underlying_transport(self) -> None:
        """Verify close method delegates directly to underlying transport."""

        inner = DummyTransport()
        layer = ConcreteTransportLayer(inner)

        layer.close()

        assert inner.is_closed is True
        assert layer.is_closed is True

    def test_transport_layer_context_manager_scope__closes_underlying_transport_on_exit(self) -> None:
        """Verify context manager protocol closes the underlying transport on exit."""

        inner = DummyTransport()

        with ConcreteTransportLayer(inner) as layer:
            assert layer.is_closed is False
            assert inner.is_closed is False

        assert inner.is_closed is True
        assert layer.is_closed is True

    def test_transport_layer_context_manager_scope__exception_raised__closes_on_exit(self) -> None:
        """Verify context manager closes underlying transport even when exception is raised."""

        inner = DummyTransport()

        with pytest.raises(RuntimeError, match="layer failure"):
            with ConcreteTransportLayer(inner) as layer:
                raise RuntimeError("layer failure")

        assert inner.is_closed is True
        assert layer.is_closed is True

    def test_transport_layer_stacked_layers__delegate_lifecycle_recursively(self) -> None:
        """Verify nested transport layers delegate lifecycle operations through the stack."""

        inner = DummyTransport(incoming_data=b"nested_payload")
        layer1 = ConcreteTransportLayer(inner)
        layer2 = ConcreteTransportLayer(layer1)

        assert layer2.underlying is layer1
        assert layer1.underlying is inner

        layer2.write(b"outbound_nested")

        assert inner.written_bytes == b"outbound_nested"
        assert layer2.read(4096) == b"nested_payload"

        layer2.close()

        assert inner.is_closed is True
        assert layer1.is_closed is True
        assert layer2.is_closed is True

    def test_transport_layer_read_and_write__forwards_through_underlying_transport(self) -> None:
        """Verify concrete transport layer forwards read and write payloads."""

        inner = DummyTransport(incoming_data=b"stream_bytes")
        layer = ConcreteTransportLayer(inner)

        layer.write(b"payload_bytes")
        received = layer.read(4096)

        assert inner.written_bytes == b"payload_bytes"
        assert received == b"stream_bytes"
