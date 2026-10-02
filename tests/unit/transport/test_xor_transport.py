import pytest

from declusor import testing, transport


def test_xor_transport_empty_key_raises_value_error() -> None:
    """Verify XorTransport rejects empty keys."""

    raw_trans = testing.DummyTransport()
    with pytest.raises(ValueError, match="XOR key cannot be empty"):
        transport.XorTransport(raw_trans, b"")


def test_xor_transport_roundtrip_plaintext_recovery() -> None:
    """Verify bidirectional encryption and decryption recovers plaintext perfectly."""

    raw_a, raw_b = testing.create_memory_transport_pair()
    try:
        key = b"transport_secret_cipher_key"
        xor_a = transport.XorTransport(raw_a, key)
        xor_b = transport.XorTransport(raw_b, key)

        message = b"Security payload test through encrypted transport"
        xor_a.write(message)

        # Confirm the underlying raw transport carried ciphertext (not plaintext)
        # We read via xor_b to decrypt
        decrypted = xor_b.read(4096)
        assert decrypted == message
    finally:
        raw_a.close()
        raw_b.close()


def test_xor_transport_underlying_data_is_obfuscated() -> None:
    """Verify data transmitted over underlying transport is indeed ciphered."""

    raw_a, raw_b = testing.create_memory_transport_pair()
    try:
        key = b"secret_key"
        xor_a = transport.XorTransport(raw_a, key)

        message = b"Sensitive plaintext token"
        xor_a.write(message)

        # Directly read raw bytes from raw_b without decrypting
        raw_bytes = raw_b.read(4096)
        assert raw_bytes != message
        assert len(raw_bytes) == len(message)
    finally:
        raw_a.close()
        raw_b.close()


def test_xor_transport_stream_fragmentation_resilience() -> None:
    """Verify arbitrary packet fragmentation does not desynchronize the cipher."""

    raw_a, raw_b = testing.create_memory_transport_pair()
    try:
        key = b"prime_len_key_7"
        xor_a = transport.XorTransport(raw_a, key)
        xor_b = transport.XorTransport(raw_b, key)

        # Write in 3 chunks of irregular sizes
        chunk1 = b"ABCDEFGHIJ"  # 10 bytes
        chunk2 = b"1234567890!@#$%^"  # 16 bytes
        chunk3 = b"Ending stream segment"  # 21 bytes

        xor_a.write(chunk1)
        xor_a.write(chunk2)
        xor_a.write(chunk3)

        # Read on destination in completely different chunk sizes
        part1 = xor_b.read_exact(5)
        part2 = xor_b.read_exact(15)
        part3 = xor_b.read_exact(27)

        reassembled = part1 + part2 + part3
        assert reassembled == chunk1 + chunk2 + chunk3
    finally:
        raw_a.close()
        raw_b.close()


def test_xor_transport_timeout_delegation() -> None:
    """Verify timeout get and set delegate directly to underlying transport."""

    raw = testing.DummyTransport()
    xor_trans = transport.XorTransport(raw, b"key")

    assert xor_trans.timeout is None
    xor_trans.timeout = 1.5
    assert xor_trans.timeout == 1.5
    assert raw.timeout == 1.5


def test_xor_transport_close_delegates_to_underlying() -> None:
    """Verify closing XorTransport closes the underlying transport."""

    raw = testing.DummyTransport()
    xor_trans = transport.XorTransport(raw, b"key")

    assert not xor_trans.is_closed
    xor_trans.close()
    assert xor_trans.is_closed
    assert raw.is_closed
