import queue
from collections.abc import Sequence

from declusor import config, contract


class DummyTransport(contract.ITransport):
    """In-memory test double for ITransport.

    Records written bytes and replays pre-configured incoming chunks without
    network socket interaction. Allows simulating errors on next read or write.
    """

    def __init__(
        self,
        incoming_data: bytes | list[bytes] | None = None,
        *,
        peer_address: str = "127.0.0.1:54321",
    ) -> None:
        """Initialize with optional pre-loaded incoming data and remote address."""

        self._peer_address = peer_address
        self._closed = False
        self._timeout: float | None = None
        self._incoming: list[bytes] = []

        if isinstance(incoming_data, bytes):
            self._incoming.append(incoming_data)
        elif incoming_data is not None:
            self._incoming.extend(incoming_data)

        self._written = bytearray()
        self._write_history: list[bytes] = []
        self._simulated_read_error: Exception | None = None
        self._simulated_write_error: Exception | None = None

    @property
    def is_closed(self) -> bool:
        """Return True if the transport is closed."""

        return self._closed

    @property
    def timeout(self) -> float | None:
        """Transport I/O timeout in seconds."""

        return self._timeout

    @timeout.setter
    def timeout(self, value: float | None, /) -> None:
        """Set transport I/O timeout in seconds."""

        self._timeout = value

    @property
    def peer_address(self) -> str:
        """Representation of the remote endpoint."""

        return self._peer_address

    @property
    def written_bytes(self) -> bytes:
        """Return all bytes accumulated from write calls."""

        return bytes(self._written)

    @property
    def write_history(self) -> list[bytes]:
        """Return individual chunks passed to each write call."""

        return list(self._write_history)

    def push_incoming(self, data: bytes, /) -> None:
        """Enqueue incoming data for subsequent read calls."""

        self._incoming.append(data)

    def simulate_error_on_next_read(self, error: Exception, /) -> None:
        """Configure an exception to be raised on the next read call."""

        self._simulated_read_error = error

    def simulate_error_on_next_write(self, error: Exception, /) -> None:
        """Configure an exception to be raised on the next write call."""

        self._simulated_write_error = error

    def read(self, max_bytes: int = 4096, /) -> bytes:
        """Read queued incoming bytes."""

        if self._closed:
            raise config.ConnectionClosed("Cannot read from closed transport.")

        if self._simulated_read_error is not None:
            err = self._simulated_read_error
            self._simulated_read_error = None
            raise err

        if not self._incoming:
            return b""

        chunk = self._incoming.pop(0)

        if len(chunk) <= max_bytes:
            return chunk

        self._incoming.insert(0, chunk[max_bytes:])

        return chunk[:max_bytes]

    def write(self, data: bytes, /) -> None:
        """Record written bytes."""

        if self._closed:
            raise config.ConnectionClosed("Cannot write to closed transport.")

        if self._simulated_write_error is not None:
            err = self._simulated_write_error
            self._simulated_write_error = None
            raise err

        self._written.extend(data)
        self._write_history.append(data)

    def close(self) -> None:
        """Close the transport idempotently."""

        self._closed = True


class MemoryTransport(contract.ITransport):
    """Full-duplex in-memory transport channel.

    Operates via thread-safe FIFO queues, allowing communication between two
    MemoryTransport endpoints without binding network sockets.
    """

    def __init__(
        self,
        inbox: queue.Queue[bytes | None],
        outbox: queue.Queue[bytes | None],
        peer_address: str,
    ) -> None:
        """Initialize with inbox/outbox queues and remote peer description."""

        self._inbox = inbox
        self._outbox = outbox
        self._peer_address = peer_address
        self._closed = False
        self._timeout: float | None = None
        self._leftover = bytearray()
        self._peer_closed = False

    @property
    def is_closed(self) -> bool:
        """Return True if this transport endpoint is closed."""

        return self._closed

    @property
    def timeout(self) -> float | None:
        """Transport I/O timeout in seconds."""

        return self._timeout

    @timeout.setter
    def timeout(self, value: float | None, /) -> None:
        """Set transport I/O timeout in seconds."""

        self._timeout = value

    @property
    def peer_address(self) -> str:
        """Peer endpoint address."""

        return self._peer_address

    def read(self, max_bytes: int = 4096, /) -> bytes:
        """Read bytes from the inbox queue."""

        if self._closed:
            raise config.ConnectionClosed("Cannot read from closed transport.")

        if self._leftover:
            chunk = bytes(self._leftover[:max_bytes])
            del self._leftover[:max_bytes]
            return chunk

        if self._peer_closed:
            return b""

        try:
            data = self._inbox.get(block=True, timeout=self._timeout)
        except queue.Empty as err:
            raise config.ConnectionTimeoutError(f"Timed out waiting for memory transport read after {self._timeout}s.") from err

        if data is None:
            self._peer_closed = True
            return b""

        if len(data) <= max_bytes:
            return data

        self._leftover.extend(data[max_bytes:])

        return data[:max_bytes]

    def write(self, data: bytes, /) -> None:
        """Write bytes to the outbox queue."""

        if self._closed:
            raise config.ConnectionClosed("Cannot write to closed transport.")

        if not data:
            return

        self._outbox.put(data)

    def close(self) -> None:
        """Close this endpoint and signal EOF to the peer."""

        if self._closed:
            return

        self._closed = True
        self._outbox.put(None)


def create_memory_transport_pair(
    endpoint_a: str = "memory://client",
    endpoint_b: str = "memory://server",
) -> tuple[MemoryTransport, MemoryTransport]:
    """Create an interconnected pair of in-memory duplex transports."""

    q_a_to_b: queue.Queue[bytes | None] = queue.Queue()
    q_b_to_a: queue.Queue[bytes | None] = queue.Queue()

    trans_a = MemoryTransport(inbox=q_b_to_a, outbox=q_a_to_b, peer_address=endpoint_b)
    trans_b = MemoryTransport(inbox=q_a_to_b, outbox=q_b_to_a, peer_address=endpoint_a)

    return trans_a, trans_b


class MemoryTransportListener(contract.ITransportListener):
    """In-memory transport listener double for testing server lifecycles without sockets."""

    def __init__(
        self,
        endpoint: str = "memory://listener",
        *,
        incoming_transports: Sequence[contract.ITransport] | None = None,
    ) -> None:
        """Initialize listener with local endpoint description and optional queued transports."""

        self._endpoint = endpoint
        self._closed = False
        self._queue: queue.Queue[contract.ITransport] = queue.Queue()
        self.accepted_count: int = 0

        if incoming_transports is not None:
            for t in incoming_transports:
                self.enqueue_transport(t)

    @property
    def local_endpoint(self) -> str:
        """Return the local listening endpoint description."""

        return self._endpoint

    @property
    def is_closed(self) -> bool:
        """Return True if the listener is closed."""

        return self._closed

    def enqueue_transport(self, transport: contract.ITransport, /) -> None:
        """Enqueue an accepted transport for accept() to return."""

        self._queue.put(transport)

    def create_client(self, client_endpoint: str = "memory://client") -> MemoryTransport:
        """Create a paired MemoryTransport, enqueue the server side, and return the client."""

        client, server = create_memory_transport_pair(
            endpoint_a=client_endpoint,
            endpoint_b=self._endpoint,
        )

        self.enqueue_transport(server)

        return client

    def accept(self, timeout: float | None = None) -> contract.ITransport:
        """Return an enqueued transport, waiting up to timeout seconds."""

        if self._closed:
            raise config.ConnectionClosed("Cannot accept on closed listener.")

        try:
            transport = self._queue.get(block=True, timeout=timeout)
            self.accepted_count += 1
            return transport
        except queue.Empty as err:
            raise config.ConnectionTimeoutError(f"Timed out after {timeout}s waiting for incoming connection.") from err

    def close(self) -> None:
        """Close the listener idempotently."""

        self._closed = True
