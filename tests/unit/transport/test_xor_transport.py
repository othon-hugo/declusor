"""Unit tests for the XOR repeating-key stream obfuscation transport."""

from collections.abc import Generator

import pytest

from declusor import config, testing, transport


@pytest.fixture
def memory_transport_pair() -> Generator[tuple[testing.MemoryTransport, testing.MemoryTransport], None, None]:
    """Provide a linked bidirectional in-memory transport pair with safe teardown."""

    client, server = testing.create_memory_transport_pair()
    try:
        yield client, server
    finally:
        client.close()
        server.close()


class TestXorTransportLifecycle:
    """Tests for XorTransport initialization, properties, and lifecycle management."""

    def test_xor_transport_init__valid_key__initializes_offsets_to_zero(self) -> None:
        """Verify successful initialization with key sets stream offsets to zero."""

        raw = testing.DummyTransport()
        xor_trans = transport.XorTransport(raw, b"secret-key")

        assert xor_trans._write_offset == 0
        assert xor_trans._read_offset == 0

    def test_xor_transport_init__empty_key__raises_value_error(self) -> None:
        """Verify initialization rejects empty key with ValueError."""

        raw = testing.DummyTransport()

        with pytest.raises(ValueError, match="XOR key cannot be empty"):
            transport.XorTransport(raw, b"")

    def test_xor_transport_underlying__getter__returns_wrapped_transport(self) -> None:
        """Verify underlying property returns the decorated transport instance."""

        raw = testing.DummyTransport()
        xor_trans = transport.XorTransport(raw, b"key")

        assert xor_trans.underlying is raw

    def test_xor_transport_is_closed__open_underlying__returns_false(self) -> None:
        """Verify is_closed returns False when underlying transport is open."""

        raw = testing.DummyTransport()
        xor_trans = transport.XorTransport(raw, b"key")

        assert not xor_trans.is_closed

    def test_xor_transport_is_closed__closed_underlying__returns_true(self) -> None:
        """Verify is_closed returns True when underlying transport is closed."""

        raw = testing.DummyTransport()
        raw.close()
        xor_trans = transport.XorTransport(raw, b"key")

        assert xor_trans.is_closed

    def test_xor_transport_close__open_transport__closes_underlying_transport(self) -> None:
        """Verify close delegates directly to the underlying transport."""

        raw = testing.DummyTransport()
        xor_trans = transport.XorTransport(raw, b"key")

        xor_trans.close()

        assert xor_trans.is_closed
        assert raw.is_closed

    def test_xor_transport_close__repeated_calls__is_idempotent(self) -> None:
        """Verify calling close multiple times does not raise an error."""

        raw = testing.DummyTransport()
        xor_trans = transport.XorTransport(raw, b"key")

        xor_trans.close()
        xor_trans.close()

        assert xor_trans.is_closed

    def test_xor_transport_context_manager__exit__closes_underlying_transport(self) -> None:
        """Verify context manager automatically closes the transport on exit."""

        raw = testing.DummyTransport()

        with transport.XorTransport(raw, b"key") as xor_trans:
            assert not xor_trans.is_closed

        assert xor_trans.is_closed
        assert raw.is_closed

    def test_xor_transport_timeout__getter_and_setter__delegates_to_underlying_transport(self) -> None:
        """Verify timeout getter and setter delegate directly to the underlying transport."""

        raw = testing.DummyTransport()
        xor_trans = transport.XorTransport(raw, b"key")

        assert xor_trans.timeout is None

        xor_trans.timeout = 2.5

        assert xor_trans.timeout == 2.5
        assert raw.timeout == 2.5

    def test_xor_transport_peer_address__getter__delegates_to_underlying_transport(self) -> None:
        """Verify peer_address property delegates to the underlying transport."""

        raw = testing.DummyTransport()
        xor_trans = transport.XorTransport(raw, b"key")

        assert xor_trans.peer_address == raw.peer_address


class TestXorTransportEgress:
    """Tests for XorTransport write operations and egress encryption."""

    def test_xor_transport_write__empty_bytes__is_noop_without_forwarding_or_advancing_offset(self) -> None:
        """Verify write(b'') does not transmit to underlying or advance write offset."""

        raw = testing.DummyTransport()
        xor_trans = transport.XorTransport(raw, b"key")

        xor_trans.write(b"")

        assert raw.written_bytes == b""
        assert xor_trans._write_offset == 0

    def test_xor_transport_write__non_empty_bytes__forwards_encrypted_bytes_to_underlying(self) -> None:
        """Verify write encrypts bytes with key and transmits ciphertext to underlying transport."""

        raw = testing.DummyTransport()
        xor_trans = transport.XorTransport(raw, b"K")

        xor_trans.write(b"A")

        # 'A' (65) ^ 'K' (75) = 10 (b"\n")
        assert raw.written_bytes == bytes([ord("A") ^ ord("K")])
        assert xor_trans._write_offset == 0  # 1 byte len with 1 byte key wraps to 0

    def test_xor_transport_write__multiple_chunks__advances_write_offset_across_key_boundaries(self) -> None:
        """Verify sequential writes maintain continuous keystream alignment."""

        raw = testing.DummyTransport()
        key = b"KEY"  # 3 bytes
        xor_trans = transport.XorTransport(raw, key)

        xor_trans.write(b"AB")  # offsets 0, 1 -> next is 2
        assert xor_trans._write_offset == 2

        xor_trans.write(b"CD")  # offset 2, then (2+2)%3 = 1 -> next is 1
        assert xor_trans._write_offset == 1

        expected = bytes(
            [
                ord("A") ^ ord("K"),
                ord("B") ^ ord("E"),
                ord("C") ^ ord("Y"),
                ord("D") ^ ord("K"),
            ]
        )
        assert raw.written_bytes == expected

    def test_xor_transport_write__single_byte_key__applies_uniform_byte_mask(self) -> None:
        """Verify single-byte key uniformly masks every byte."""

        raw = testing.DummyTransport()
        xor_trans = transport.XorTransport(raw, b"\xff")

        xor_trans.write(b"\x00\x0f\xf0\xff")

        assert raw.written_bytes == b"\xff\xf0\x0f\x00"

    def test_xor_transport_write__underlying_error__propagates_exception(self) -> None:
        """Verify exceptions raised by underlying transport write propagate outwards."""

        raw = testing.DummyTransport()
        raw.close()
        xor_trans = transport.XorTransport(raw, b"key")

        with pytest.raises(config.ConnectionClosed, match="Cannot write to closed transport"):
            xor_trans.write(b"payload")


class TestXorTransportIngress:
    """Tests for XorTransport read operations and ingress decryption."""

    def test_xor_transport_read__eof_empty_bytes__returns_empty_bytes_without_advancing_offset(self) -> None:
        """Verify read on EOF returns empty bytes without advancing read offset."""

        raw = testing.DummyTransport(incoming_data=b"")
        xor_trans = transport.XorTransport(raw, b"key")

        data = xor_trans.read(1024)

        assert data == b""
        assert xor_trans._read_offset == 0

    def test_xor_transport_read__encrypted_chunk__decrypts_and_advances_read_offset(self) -> None:
        """Verify read decrypts ciphertext chunk and advances read offset."""

        # 'A' ^ 'K' = ciphertext
        ciphertext = bytes([ord("A") ^ ord("K")])
        raw = testing.DummyTransport(incoming_data=ciphertext)
        xor_trans = transport.XorTransport(raw, b"KEY")

        decrypted = xor_trans.read(1024)

        assert decrypted == b"A"
        assert xor_trans._read_offset == 1

    def test_xor_transport_read__multiple_chunks__advances_read_offset_across_key_boundaries(self) -> None:
        """Verify multiple read chunks decrypt seamlessly across key wraparound boundaries."""

        raw_a, raw_b = testing.create_memory_transport_pair()
        try:
            key = b"KEY"  # 3 bytes
            xor_writer = transport.XorTransport(raw_a, key)
            xor_reader = transport.XorTransport(raw_b, key)

            xor_writer.write(b"ABCDE")

            part1 = xor_reader.read(2)
            part2 = xor_reader.read(3)

            assert part1 == b"AB"
            assert part2 == b"CDE"
            assert xor_reader._read_offset == 2  # 5 % 3 = 2
        finally:
            raw_a.close()
            raw_b.close()

    def test_xor_transport_read__default_max_bytes__reads_up_to_4096_bytes(self) -> None:
        """Verify default argument for read requests up to 4096 bytes."""

        raw = testing.DummyTransport(incoming_data=b"\x00" * 10)
        xor_trans = transport.XorTransport(raw, b"\x00")

        result = xor_trans.read()

        assert len(result) == 10

    def test_xor_transport_read__underlying_error__propagates_exception(self) -> None:
        """Verify exceptions raised by underlying transport read propagate outwards."""

        raw = testing.DummyTransport()
        raw.close()
        xor_trans = transport.XorTransport(raw, b"key")

        with pytest.raises(config.ConnectionClosed, match="Cannot read from closed transport"):
            xor_trans.read(1024)


class TestXorTransportEndToEnd:
    """Tests for full bidirectional streaming, fragmentation, and keystream isolation."""

    def test_xor_transport_roundtrip__direct_payload__recovers_exact_plaintext(
        self,
        memory_transport_pair: tuple[testing.MemoryTransport, testing.MemoryTransport],
    ) -> None:
        """Verify complete roundtrip transmission recovers identical plaintext."""

        client_raw, server_raw = memory_transport_pair
        key = b"test-secret-cipher-key"
        client = transport.XorTransport(client_raw, key)
        server = transport.XorTransport(server_raw, key)

        message = b"Security payload test through encrypted transport"
        client.write(message)

        decrypted = server.read(len(message))
        assert decrypted == message

    def test_xor_transport_roundtrip__arbitrary_fragmentation__recovers_exact_plaintext(
        self,
        memory_transport_pair: tuple[testing.MemoryTransport, testing.MemoryTransport],
    ) -> None:
        """Verify mismatched write and read chunk sizes preserve continuous keystream alignment."""

        client_raw, server_raw = memory_transport_pair
        key = b"prime_len_key_7"
        client = transport.XorTransport(client_raw, key)
        server = transport.XorTransport(server_raw, key)

        chunk1 = b"ABCDEFGHIJ"
        chunk2 = b"1234567890!@#$%^"
        chunk3 = b"Ending stream segment"

        client.write(chunk1)
        client.write(chunk2)
        client.write(chunk3)

        part1 = server.read_exact(5)
        part2 = server.read_exact(15)
        part3 = server.read_exact(27)

        assert part1 + part2 + part3 == chunk1 + chunk2 + chunk3

    def test_xor_transport_roundtrip__offsets_independence__egress_and_ingress_do_not_interfere(
        self,
        memory_transport_pair: tuple[testing.MemoryTransport, testing.MemoryTransport],
    ) -> None:
        """Verify egress writing and ingress reading maintain isolated offsets on the same transport instance."""

        node_a_raw, node_b_raw = memory_transport_pair
        key = b"duplex_key"
        node_a = transport.XorTransport(node_a_raw, key)
        node_b = transport.XorTransport(node_b_raw, key)

        # Node A writes 5 bytes
        node_a.write(b"HELLO")
        assert node_a._write_offset == 5
        assert node_a._read_offset == 0

        # Node B reads 5 bytes
        assert node_b.read(5) == b"HELLO"
        assert node_b._read_offset == 5
        assert node_b._write_offset == 0

        # Node B replies with 4 bytes
        node_b.write(b"ECHO")
        assert node_b._write_offset == 4
        assert node_b._read_offset == 5

        # Node A reads 4 bytes
        assert node_a.read(4) == b"ECHO"
        assert node_a._read_offset == 4
        assert node_a._write_offset == 5
