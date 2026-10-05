"""Tests for the public exports of declusor.transport."""

from declusor import transport


class TestTransportExports:
    """Verify the canonical public transport API."""

    def test_transport_exports__canonical_symbols__are_accessible(self) -> None:
        """Every declared public transport symbol is exported and accessible."""

        expected = [
            "ConnectionClosed",
            "ConnectionError",
            "ConnectionTimeoutError",
            "default_transport_registry",
            "SocketTransport",
            "TcpListener",
            "TransportLayerFactory",
            "TransportLayerRegistry",
            "TransportPipeline",
            "XorTransport",
        ]

        assert sorted(transport.__all__) == sorted(expected)
        for symbol in expected:
            assert hasattr(transport, symbol), f"declusor.transport is missing export: {symbol}"
            assert not symbol.startswith("_")
