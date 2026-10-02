import pytest

from declusor import contract, testing, transport


class PrefixTransport(contract.ITransportLayer):
    """Test transport layer that prepends a prefix on write and strips on read."""

    def __init__(self, inner: contract.ITransport, prefix: bytes = b"PREFIX:") -> None:
        super().__init__(inner)
        self._prefix = prefix

    def read(self, max_bytes: int = 4096, /) -> bytes:
        data = self._transport.read(max_bytes)
        if data.startswith(self._prefix):
            return data[len(self._prefix) :]
        return data

    def write(self, data: bytes, /) -> None:
        self._transport.write(self._prefix + data)


def test_transport_pipeline_empty_passthrough() -> None:
    """Empty TransportPipeline must return the base transport unchanged."""

    pipeline = transport.TransportPipeline()
    inner = testing.DummyTransport(incoming_data=b"raw")

    wrapped = pipeline.wrap(inner)
    assert wrapped is inner
    assert wrapped.read(1024) == b"raw"


def test_transport_pipeline_single_layer() -> None:
    """TransportPipeline with one layer must wrap base transport."""

    pipeline = transport.TransportPipeline([lambda t: PrefixTransport(t, b"A:")])
    inner = testing.DummyTransport(incoming_data=b"A:hello")

    wrapped = pipeline.wrap(inner)
    assert isinstance(wrapped, PrefixTransport)
    assert wrapped.read(1024) == b"hello"

    wrapped.write(b"out")
    assert inner.written_bytes == b"A:out"


def test_transport_pipeline_multiple_layers_sequential_order() -> None:
    """TransportPipeline with multiple layers must wrap in sequential order."""

    pipeline = transport.TransportPipeline(
        [
            lambda t: PrefixTransport(t, b"INNER:"),
            lambda t: PrefixTransport(t, b"OUTER:"),
        ]
    )
    inner = testing.DummyTransport()
    wrapped = pipeline.wrap(inner)

    wrapped.write(b"data")
    # Outer layer prepends OUTER:, then inner layer prepends INNER:
    assert inner.written_bytes == b"INNER:OUTER:data"


def test_transport_layer_registry_register_and_get() -> None:
    """Registry must store and retrieve factories by case-insensitive name."""

    registry = transport.TransportLayerRegistry()
    registry.register("prefix", lambda t: PrefixTransport(t, b"P:"))

    factory = registry.get("PREFIX")
    inner = testing.DummyTransport()
    wrapped = factory(inner)

    assert isinstance(wrapped, PrefixTransport)
    assert registry.names() == ("prefix",)


def test_transport_layer_registry_rejects_empty_name() -> None:
    """Registry must raise ValueError on empty or whitespace name."""

    registry = transport.TransportLayerRegistry()

    with pytest.raises(ValueError, match="cannot be empty"):
        registry.register("   ", lambda t: t)


def test_transport_layer_registry_get_unknown_raises_key_error() -> None:
    """Registry must raise KeyError with available names when layer is not found."""

    registry = transport.TransportLayerRegistry()
    registry.register("xor", lambda t: t)

    with pytest.raises(KeyError, match="Unknown transport layer: 'aes'"):
        registry.get("aes")


def test_transport_layer_registry_build_pipeline() -> None:
    """Registry must build a configured TransportPipeline from a sequence of names."""

    registry = transport.TransportLayerRegistry()
    registry.register("p1", lambda t: PrefixTransport(t, b"1:"))
    registry.register("p2", lambda t: PrefixTransport(t, b"2:"))

    pipeline = registry.build_pipeline(["p1", "p2"])
    assert len(pipeline.layers) == 2

    inner = testing.DummyTransport()
    wrapped = pipeline.wrap(inner)
    wrapped.write(b"test")
    assert inner.written_bytes == b"1:2:test"


def test_default_transport_registry_contains_xor() -> None:
    """Default transport registry must contain 'xor' pre-registered with default key."""

    registry = transport.default_transport_registry()
    assert "xor" in registry.names()

    inner = testing.DummyTransport()
    factory = registry.get("xor")
    wrapped = factory(inner)

    assert isinstance(wrapped, transport.XorTransport)
    # Write through XOR, underlying should have ciphered bytes using DEFAULT_XOR_KEY
    wrapped.write(b"sensitive")
    assert inner.written_bytes != b"sensitive"
    assert len(inner.written_bytes) == len(b"sensitive")
