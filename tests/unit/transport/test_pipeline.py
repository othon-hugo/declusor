"""Unit tests for the transport pipeline and layer registry."""

from collections.abc import Generator

import pytest

from declusor import contract, testing, transport


class PrefixTransport(contract.ITransportLayer):
    """Deterministic test transport layer that prepends a prefix on write and strips on read."""

    def __init__(self, inner: contract.ITransport, prefix: bytes = b"PREFIX:") -> None:
        """Initialize with inner transport and byte prefix."""

        super().__init__(inner)
        self._prefix = prefix

    def read(self, max_bytes: int = 4096, /) -> bytes:
        """Read from inner transport and strip prefix if present."""

        data = self._transport.read(max_bytes)
        if data.startswith(self._prefix):
            return data[len(self._prefix) :]
        return data

    def write(self, data: bytes, /) -> None:
        """Prepend prefix and forward to inner transport."""

        self._transport.write(self._prefix + data)


@pytest.fixture
def memory_transport_pair() -> Generator[tuple[testing.MemoryTransport, testing.MemoryTransport], None, None]:
    """Provide a linked bidirectional in-memory transport pair with safe teardown."""

    client, server = testing.create_memory_transport_pair()
    try:
        yield client, server
    finally:
        client.close()
        server.close()


class TestTransportPipeline:
    """Tests for TransportPipeline."""

    def test_transport_pipeline_init__default_layers__is_empty_tuple(self) -> None:
        """Verify default initialization produces an empty layers tuple."""

        pipeline = transport.TransportPipeline()

        assert pipeline.layers == ()

    def test_transport_pipeline_init__mutable_sequence__creates_defensive_copy(self) -> None:
        """Verify pipeline creates a defensive tuple copy of the provided layer sequence."""

        layer_list: list[transport.TransportLayerFactory] = [lambda t: PrefixTransport(t, b"A:")]
        pipeline = transport.TransportPipeline(layer_list)

        layer_list.append(lambda t: PrefixTransport(t, b"B:"))

        assert len(pipeline.layers) == 1

    def test_transport_pipeline_wrap__empty_layers__returns_base_transport_identity(self) -> None:
        """Verify wrapping with empty layers returns the exact base transport instance."""

        pipeline = transport.TransportPipeline()
        base = testing.DummyTransport(incoming_data=b"raw-payload")

        wrapped = pipeline.wrap(base)

        assert wrapped is base

    def test_transport_pipeline_wrap__single_layer__applies_layer_to_transport(self) -> None:
        """Verify a single layer wraps the base transport and transforms data."""

        pipeline = transport.TransportPipeline([lambda t: PrefixTransport(t, b"HDR:")])
        base = testing.DummyTransport()

        wrapped = pipeline.wrap(base)
        wrapped.write(b"payload")

        assert isinstance(wrapped, PrefixTransport)
        assert base.written_bytes == b"HDR:payload"

    def test_transport_pipeline_wrap__multiple_layers__stacks_layers_in_sequential_write_order(self) -> None:
        """Verify multiple layers nest sequentially during write operations."""

        pipeline = transport.TransportPipeline(
            [
                lambda t: PrefixTransport(t, b"INNER:"),
                lambda t: PrefixTransport(t, b"OUTER:"),
            ]
        )
        base = testing.DummyTransport()

        wrapped = pipeline.wrap(base)
        wrapped.write(b"data")

        assert base.written_bytes == b"INNER:OUTER:data"

    def test_transport_pipeline_wrap__multiple_layers__unwraps_layers_in_sequential_read_order(self) -> None:
        """Verify multiple layers unwrap data in symmetrical order during read operations."""

        pipeline = transport.TransportPipeline(
            [
                lambda t: PrefixTransport(t, b"INNER:"),
                lambda t: PrefixTransport(t, b"OUTER:"),
            ]
        )
        base = testing.DummyTransport(incoming_data=b"INNER:OUTER:data")

        wrapped = pipeline.wrap(base)

        assert wrapped.read(1024) == b"data"


class TestTransportLayerRegistry:
    """Tests for TransportLayerRegistry."""

    def test_transport_layer_registry_init__initially_empty__names_returns_empty_tuple(self) -> None:
        """Verify a newly initialized registry has no registered layer names."""

        registry = transport.TransportLayerRegistry()

        assert registry.names() == ()

    def test_transport_layer_registry_register__valid_factory__stores_under_normalized_name(self) -> None:
        """Verify registration stores the factory under a normalized name."""

        registry = transport.TransportLayerRegistry()
        registry.register("prefix", lambda t: PrefixTransport(t, b"P:"))

        assert "prefix" in registry.names()

    def test_transport_layer_registry_register__mixed_case_and_whitespace__normalizes_name(self) -> None:
        """Verify layer names are stripped of whitespace and converted to lowercase."""

        registry = transport.TransportLayerRegistry()
        registry.register("  EnCrYpT  ", lambda t: PrefixTransport(t, b"E:"))

        assert registry.names() == ("encrypt",)

    def test_transport_layer_registry_register__duplicate_name__overwrites_existing_factory(self) -> None:
        """Verify registering under an existing name replaces the previously registered factory."""

        registry = transport.TransportLayerRegistry()
        registry.register("layer", lambda t: PrefixTransport(t, b"OLD:"))
        registry.register("layer", lambda t: PrefixTransport(t, b"NEW:"))

        factory = registry.get("layer")
        base = testing.DummyTransport()
        wrapped = factory(base)
        wrapped.write(b"data")

        assert base.written_bytes == b"NEW:data"

    def test_transport_layer_registry_register__empty_name__raises_value_error(self) -> None:
        """Verify registering with an empty string name raises ValueError."""

        registry = transport.TransportLayerRegistry()

        with pytest.raises(ValueError, match="Transport layer name cannot be empty"):
            registry.register("", lambda t: t)

    def test_transport_layer_registry_register__whitespace_only_name__raises_value_error(self) -> None:
        """Verify registering with a whitespace-only name raises ValueError."""

        registry = transport.TransportLayerRegistry()

        with pytest.raises(ValueError, match="Transport layer name cannot be empty"):
            registry.register("   \t\n  ", lambda t: t)

    def test_transport_layer_registry_get__registered_name__returns_factory(self) -> None:
        """Verify get retrieves the registered factory callable."""

        registry = transport.TransportLayerRegistry()
        registry.register("xor", lambda t: PrefixTransport(t, b"X:"))

        factory = registry.get("xor")
        base = testing.DummyTransport()
        wrapped = factory(base)

        assert isinstance(wrapped, PrefixTransport)

    def test_transport_layer_registry_get__case_insensitive_and_untrimmed__returns_factory(self) -> None:
        """Verify get normalizes the lookup key with strip and lowercase."""

        registry = transport.TransportLayerRegistry()
        registry.register("custom", lambda t: PrefixTransport(t, b"C:"))

        factory = registry.get("  CUSTOM  ")
        base = testing.DummyTransport()
        wrapped = factory(base)

        assert isinstance(wrapped, PrefixTransport)

    def test_transport_layer_registry_get__unregistered_name__raises_key_error_with_available_names(self) -> None:
        """Verify get on unknown name raises KeyError displaying available layer names."""

        registry = transport.TransportLayerRegistry()
        registry.register("alpha", lambda t: t)
        registry.register("beta", lambda t: t)

        with pytest.raises(KeyError, match=r"Unknown transport layer: 'gamma'\. Available: \('alpha', 'beta'\)"):
            registry.get("gamma")

    def test_transport_layer_registry_names__multiple_entries__returns_alphabetically_sorted_tuple(self) -> None:
        """Verify names returns a sorted tuple of all registered names."""

        registry = transport.TransportLayerRegistry()
        registry.register("zebra", lambda t: t)
        registry.register("alpha", lambda t: t)
        registry.register("middle", lambda t: t)

        assert registry.names() == ("alpha", "middle", "zebra")

    def test_transport_layer_registry_build_pipeline__empty_names__returns_empty_pipeline(self) -> None:
        """Verify building pipeline with empty layer name sequence produces empty pipeline."""

        registry = transport.TransportLayerRegistry()

        pipeline = registry.build_pipeline([])

        assert pipeline.layers == ()

    def test_transport_layer_registry_build_pipeline__registered_names__returns_pipeline_with_factories(self) -> None:
        """Verify building pipeline resolves layer names into sequential factories."""

        registry = transport.TransportLayerRegistry()
        registry.register("first", lambda t: PrefixTransport(t, b"1:"))
        registry.register("second", lambda t: PrefixTransport(t, b"2:"))

        pipeline = registry.build_pipeline(["first", "second"])
        base = testing.DummyTransport()
        wrapped = pipeline.wrap(base)
        wrapped.write(b"test")

        assert len(pipeline.layers) == 2
        assert base.written_bytes == b"1:2:test"

    def test_transport_layer_registry_build_pipeline__case_insensitive_names__resolves_correctly(self) -> None:
        """Verify build_pipeline resolves layer names case-insensitively."""

        registry = transport.TransportLayerRegistry()
        registry.register("layer", lambda t: PrefixTransport(t, b"L:"))

        pipeline = registry.build_pipeline(["  LAYER  "])
        base = testing.DummyTransport()
        wrapped = pipeline.wrap(base)
        wrapped.write(b"data")

        assert base.written_bytes == b"L:data"

    def test_transport_layer_registry_build_pipeline__repeated_names__stacks_factories(self) -> None:
        """Verify build_pipeline correctly applies repeated layer occurrences."""

        registry = transport.TransportLayerRegistry()
        registry.register("wrap", lambda t: PrefixTransport(t, b"W:"))

        pipeline = registry.build_pipeline(["wrap", "wrap"])
        base = testing.DummyTransport()
        wrapped = pipeline.wrap(base)
        wrapped.write(b"data")

        assert base.written_bytes == b"W:W:data"

    def test_transport_layer_registry_build_pipeline__unknown_name__raises_key_error(self) -> None:
        """Verify build_pipeline raises KeyError when any requested layer is unregistered."""

        registry = transport.TransportLayerRegistry()
        registry.register("known", lambda t: t)

        with pytest.raises(KeyError, match="Unknown transport layer: 'missing'"):
            registry.build_pipeline(["known", "missing"])


class TestDefaultTransportRegistry:
    """Tests for default_transport_registry."""

    def test_default_transport_registry__names__contains_xor_layer(self) -> None:
        """Verify default transport registry pre-registers the 'xor' layer."""

        registry = transport.default_transport_registry()

        assert "xor" in registry.names()

    def test_default_transport_registry__xor_factory__wraps_in_xor_transport(self) -> None:
        """Verify the 'xor' factory wraps an incoming transport in XorTransport."""

        registry = transport.default_transport_registry()
        factory = registry.get("xor")
        base = testing.DummyTransport()

        wrapped = factory(base)

        assert isinstance(wrapped, transport.XorTransport)

    def test_default_transport_registry__xor_factory__enciphers_data_with_default_xor_key(self) -> None:
        """Verify data written through the 'xor' layer is enciphered using DEFAULT_XOR_KEY."""

        registry = transport.default_transport_registry()
        factory = registry.get("xor")
        base = testing.DummyTransport()

        wrapped = factory(base)
        wrapped.write(b"plaintext-secret")

        assert base.written_bytes != b"plaintext-secret"
        assert len(base.written_bytes) == len(b"plaintext-secret")

    def test_default_transport_registry__xor_factory__roundtrip_recovers_plaintext(
        self,
        memory_transport_pair: tuple[testing.MemoryTransport, testing.MemoryTransport],
    ) -> None:
        """Verify full bidirectional roundtrip over memory transports recovers plaintext."""

        client_raw, server_raw = memory_transport_pair
        registry = transport.default_transport_registry()

        client_xor = registry.get("xor")(client_raw)
        server_xor = registry.get("xor")(server_raw)

        message = b"Secret payload transferred through default XOR pipeline layer"
        client_xor.write(message)

        decrypted = server_xor.read(len(message))
        assert decrypted == message
