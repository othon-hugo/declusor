from declusor import contract, util


class XorTransport(contract.ITransport):
    """Obfuscates a transport byte stream using a repeating-key XOR stream cipher.

    Implements ITransport via pure interface composition, wrapping an underlying
    transport channel. Maintains independent stream offsets for write (egress) and
    read (ingress) to ensure arbitrary TCP segmentations never desynchronize the
    keystream.
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

        self._transport = transport
        self._key = key
        self._write_offset = 0
        self._read_offset = 0

    @property
    def is_closed(self) -> bool:
        """Return True if the underlying transport is closed."""

        return self._transport.is_closed

    @property
    def timeout(self) -> float | None:
        """Transport I/O timeout in seconds, or None for indefinite blocking."""

        return self._transport.timeout

    @timeout.setter
    def timeout(self, value: float | None, /) -> None:
        """Set transport I/O timeout in seconds on underlying transport."""

        self._transport.timeout = value

    @property
    def peer_address(self) -> str:
        """Remote endpoint address delegated from underlying transport."""

        return self._transport.peer_address

    @property
    def underlying_transport(self) -> contract.ITransport:
        """Access the wrapped transport instance."""

        return self._transport

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

    def close(self) -> None:
        """Close the underlying transport."""

        self._transport.close()
