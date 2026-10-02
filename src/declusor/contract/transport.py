from abc import ABC, abstractmethod
from typing import Self

from declusor import config


class ITransport(ABC):
    """Bidirectional byte-stream transport channel.

    Abstracts low-level stream communication (TCP sockets, TLS, Unix domain sockets,
    pipes, or in-memory byte streams) away from session-layer protocols.
    """

    @property
    @abstractmethod
    def is_closed(self) -> bool:
        """Return True if the transport channel is closed, False otherwise."""

        raise NotImplementedError

    @property
    @abstractmethod
    def timeout(self) -> float | None:
        """Transport I/O timeout in seconds, or None for indefinite blocking."""

        raise NotImplementedError

    @timeout.setter
    @abstractmethod
    def timeout(self, value: float | None, /) -> None:
        """Set transport I/O timeout in seconds, or None for indefinite blocking."""

        raise NotImplementedError

    @property
    @abstractmethod
    def peer_address(self) -> str:
        """Representation of the remote endpoint (e.g. '192.168.1.10:4444')."""

        raise NotImplementedError

    @abstractmethod
    def read(self, max_bytes: int = 4096, /) -> bytes:
        """Read up to max_bytes from the transport.

        Returns:
            The read bytes chunk. Returns empty bytes (b"") on EOF or remote closure.

        Raises:
            ConnectionTimeoutError: If read times out.
            ConnectionClosed: If called on a closed transport.
            ConnectionError: On general I/O or transport failure.
        """

        raise NotImplementedError

    def read_exact(self, count: int, /) -> bytes:
        """Read exactly count bytes from the transport, blocking until complete.

        Accumulates chunks defensiveliy via ``read()``.

        Args:
            count: Number of bytes to read. Must be non-negative.

        Returns:
            Exactly count bytes.

        Raises:
            ConnectionClosed: If EOF is reached before count bytes are read.
            ConnectionTimeoutError: If read times out.
            ConnectionError: On general I/O or transport failure.
            ValueError: If count < 0.
        """

        if count < 0:
            raise ValueError(f"Count must be non-negative, got {count}.")

        if count == 0:
            return b""

        buffer = bytearray()

        while len(buffer) < count:
            remaining = count - len(buffer)
            chunk = self.read(min(remaining, 4096))

            if not chunk:
                raise config.ConnectionClosed(f"Transport closed prematurely: expected {count} bytes, received {len(buffer)}.")

            buffer.extend(chunk)

        return bytes(buffer)

    @abstractmethod
    def write(self, data: bytes, /) -> None:
        """Transmit all bytes to the transport.

        Guarantees that all bytes in `data` are written before returning.

        Args:
            data: Raw bytes to send.

        Raises:
            ConnectionClosed: If called on a closed transport or remote closed.
            ConnectionTimeoutError: If transmission exceeds timeout.
            ConnectionError: On transport I/O failure.
        """

        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Close the transport and release underlying resources.

        Must be idempotent — repeated calls must not raise an error.
        """

        raise NotImplementedError

    def __enter__(self) -> Self:
        """Enter context manager, returning self."""

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context manager, closing the transport."""

        self.close()


class ITransportLayer(ITransport, ABC):
    """Abstract base for transport decorators that wrap an underlying transport.

    Provides delegation of lifecycle properties (``is_closed``, ``timeout``,
    ``peer_address``) and resource management (``close()``) to the underlying
    transport. Subclasses implement only ``read()`` and ``write()`` to
    transform the byte stream.

    This enables composable transport stacking where each layer intercepts and
    transforms data while delegating connection lifecycle to the base transport::

        raw     = SocketTransport(sock)
        xored   = XorTransport(raw, key=b"secret")
        # xored.read()  → decrypts bytes from raw.read()
        # xored.write() → encrypts bytes via raw.write()
    """

    def __init__(self, transport: ITransport, /) -> None:
        """Initialize the transport layer with an underlying transport.

        Args:
            transport: The transport to wrap and delegate lifecycle operations to.
        """

        self._transport = transport

    @property
    def underlying(self) -> ITransport:
        """The wrapped transport instance."""

        return self._transport

    @property
    def is_closed(self) -> bool:
        """Return True if the underlying transport is closed."""

        return self._transport.is_closed

    @property
    def timeout(self) -> float | None:
        """Transport I/O timeout delegated from underlying transport."""

        return self._transport.timeout

    @timeout.setter
    def timeout(self, value: float | None, /) -> None:
        """Set transport I/O timeout on the underlying transport."""

        self._transport.timeout = value

    @property
    def peer_address(self) -> str:
        """Remote endpoint address delegated from underlying transport."""

        return self._transport.peer_address

    def close(self) -> None:
        """Close the underlying transport."""

        self._transport.close()


class ITransportListener(ABC):
    """Listens for and accepts incoming transport connections."""

    @property
    @abstractmethod
    def local_endpoint(self) -> str:
        """Return the local listening endpoint description (e.g. '0.0.0.0:9000')."""

        raise NotImplementedError

    @abstractmethod
    def accept(self, timeout: float | None = None) -> ITransport:
        """Wait for and return an accepted incoming ITransport.

        Args:
            timeout: Optional seconds to wait before timing out.

        Returns:
            An active, connected ITransport instance.

        Raises:
            ConnectionTimeoutError: If timeout expires without an incoming connection.
            ConnectionClosed: If called on a closed listener.
            ConnectionError: If binding, listening, or accepting fails.
        """

        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Stop listening and release the bound port / address.

        Must be idempotent.
        """

        raise NotImplementedError

    def __enter__(self) -> Self:
        """Enter context manager, returning self."""

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context manager, closing the listener."""

        self.close()
