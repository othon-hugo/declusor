from typing import Self


class DummySocket:
    """Fully-typed fake socket object simulating OS transport without system resources."""

    def __init__(
        self,
        incoming_bytes: bytes = b"",
        peer_name: tuple[str, int] = ("127.0.0.1", 9000),
        fileno_val: int = 42,
    ) -> None:
        self._incoming: bytearray = bytearray(incoming_bytes)
        self.recv_chunks: list[bytes] = []
        self._sent: bytearray = bytearray()
        self.peer_name: tuple[str, int] = peer_name
        self.fileno_val: int = fileno_val
        self.closed: bool = False
        self.timeout: float | None = None
        self.sendall_calls: list[bytes] = []
        self.send_calls: list[bytes] = []
        self.recv_calls: list[int] = []
        self.close_calls: int = 0
        self.settimeout_calls: list[float | None] = []
        self.sendall_error: BaseException | None = None
        self.send_error: BaseException | None = None
        self.recv_error: BaseException | None = None

    @property
    def sent_bytes(self) -> bytes:
        """Return all bytes accumulated via send or sendall."""

        return bytes(self._sent)

    def feed(self, data: bytes) -> None:
        """Enqueue simulated incoming data to be read via recv."""

        self._incoming.extend(data)

    def feed_bytes(self, data: bytes) -> None:
        """Enqueue simulated incoming data to be read via recv (alias for feed)."""

        self.feed(data)

    def feed_recv_chunks(self, *chunks: bytes) -> None:
        """Enqueue individual chunk frames to be returned by successive recv() calls."""

        self.recv_chunks.extend(chunks)

    def recv(self, bufsize: int, /) -> bytes:
        """Read up to bufsize bytes from incoming buffer or pop pre-staged chunk."""

        self.recv_calls.append(bufsize)

        if self.recv_error is not None:
            raise self.recv_error

        if self.recv_chunks:
            return self.recv_chunks.pop(0)

        chunk = bytes(self._incoming[:bufsize])

        del self._incoming[:bufsize]

        return chunk

    def sendall(self, data: bytes, /) -> None:
        """Record all sent bytes and transmit to sent buffer."""

        if self.sendall_error is not None:
            raise self.sendall_error

        self.sendall_calls.append(data)
        self._sent.extend(data)

    def send(self, data: bytes, /) -> int:
        """Record all sent bytes and return count."""

        if self.send_error is not None:
            raise self.send_error

        self.send_calls.append(data)
        self._sent.extend(data)

        return len(data)

    def getpeername(self) -> tuple[str, int]:
        """Return configured peer address tuple."""

        return self.peer_name

    def settimeout(self, timeout: float | None, /) -> None:
        """Set timeout value and record call."""

        self.timeout = timeout
        self.settimeout_calls.append(timeout)

    def close(self) -> None:
        """Mark socket as closed and record invocation."""

        self.close_calls += 1
        self.closed = True

    def fileno(self) -> int:
        """Return configured fake file descriptor."""

        return self.fileno_val

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        self.close()
