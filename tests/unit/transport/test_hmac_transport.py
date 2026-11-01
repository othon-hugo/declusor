"""Tests for the standard-library HMAC transport layer."""

import threading

import pytest

from declusor import config, testing, transport


def establish_pair(
    key: bytes = b"test-shared-secret",
) -> tuple[transport.HmacTransport, transport.HmacTransport]:
    """Establish an initiator/responder pair over memory transports."""

    initiator_raw, responder_raw = testing.create_memory_transport_pair()
    initiator = transport.HmacTransport(initiator_raw, key, role="initiator")
    responder = transport.HmacTransport(responder_raw, key, role="responder")
    errors: list[BaseException] = []

    def run(layer: transport.HmacTransport) -> None:
        try:
            layer.establish()
        except BaseException as error:
            errors.append(error)

    initiator_thread = threading.Thread(target=run, args=(initiator,))
    responder_thread = threading.Thread(target=run, args=(responder,))
    initiator_thread.start()
    responder_thread.start()
    initiator_thread.join(timeout=1.0)
    responder_thread.join(timeout=1.0)

    assert not initiator_thread.is_alive()
    assert not responder_thread.is_alive()
    assert errors == []
    assert initiator.is_established
    assert responder.is_established

    return initiator, responder


class TestHmacTransport:
    """Verify mutual authentication and authenticated stream framing."""

    def test_establish__matching_keys__authenticates_both_endpoints(self) -> None:
        """Matching keys complete the mutual handshake."""

        initiator, responder = establish_pair()

        initiator.write(b"authenticated payload")

        assert responder.read(4) == b"auth"
        assert responder.read(1024) == b"enticated payload"

    def test_establish__different_keys__rejects_peer(self) -> None:
        """Different keys cannot complete the handshake."""

        initiator_raw, responder_raw = testing.create_memory_transport_pair()
        initiator = transport.HmacTransport(initiator_raw, b"initiator-key", role="initiator")
        responder = transport.HmacTransport(responder_raw, b"responder-key", role="responder")
        errors: list[BaseException] = []

        def run(layer: transport.HmacTransport) -> None:
            try:
                layer.establish()
            except BaseException as error:
                errors.append(error)

        threads = [
            threading.Thread(target=run, args=(initiator,)),
            threading.Thread(target=run, args=(responder,)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=1.0)

        assert len(errors) == 2
        assert all(isinstance(error, config.ConnectionError) for error in errors)

    def test_write__before_establish__raises_connection_error(self) -> None:
        """Application data cannot be sent before mutual authentication."""

        raw, _ = testing.create_memory_transport_pair()
        layer = transport.HmacTransport(raw, b"test-key", role="initiator")

        with pytest.raises(config.ConnectionError, match="has not been established"):
            layer.write(b"payload")

    def test_init__empty_key_or_invalid_role__raises_value_error(self) -> None:
        """Reject unusable HMAC configuration early."""

        raw, _ = testing.create_memory_transport_pair()

        with pytest.raises(ValueError, match="key cannot be empty"):
            transport.HmacTransport(raw, b"", role="initiator")

        with pytest.raises(ValueError, match="Unsupported HMAC role"):
            transport.HmacTransport(raw, b"key", role="unknown")  # type: ignore[arg-type]
