from declusor import contract, util


class XorTransport(contract.ITransportLayer):
    """Obfuscates a transport byte stream using a repeating-key XOR stream cipher.

    Wraps an underlying transport channel via ``ITransportLayer``, intercepting
    ``read()`` and ``write()`` to apply XOR transformation. Maintains
    independent stream offsets for write (egress) and read (ingress) to ensure
    arbitrary TCP segmentations never desynchronize the keystream.
    """

    def __init__(self, transport: contract.ITransport, key: bytes, /) -> None:
        """Initialize with an underlying transport and repeating encryption key.

        Args:
            transport: The underlying transport channel to decorate.
            key: Non-empty repeating XOR key.

        Raises:
            ValueError: If key is empty.
        """

        if not key:
            raise ValueError("XOR key cannot be empty.")

        super().__init__(transport)
        self._key = key
        self._write_offset = 0
        self._read_offset = 0

    def read(self, max_bytes: int = 4096, /) -> bytes:
        """Read and decrypt bytes from the underlying transport.

        Returns:
            Decrypted bytes chunk, or empty bytes on EOF.
        """

        chunk = self._transport.read(max_bytes)

        if not chunk:
            return b""

        decrypted = util.xor_bytes(chunk, self._key, offset=self._read_offset)
        self._read_offset = (self._read_offset + len(chunk)) % len(self._key)

        return decrypted

    def write(self, data: bytes, /) -> None:
        """Encrypt and transmit bytes across the underlying transport."""

        if not data:
            return

        encrypted = util.xor_bytes(data, self._key, offset=self._write_offset)
        self._transport.write(encrypted)
        self._write_offset = (self._write_offset + len(data)) % len(self._key)
