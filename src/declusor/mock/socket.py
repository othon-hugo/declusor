from typing import Any

class MockSocket:
    """A mock implementation of a socket for testing without MagicMock."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.recv_data: list[bytes] = []
        self.sent_data: list[bytes] = []
        self.peer_name: tuple[str, int] = ("127.0.0.1", 1234)
        self.timeout: float | None = None
        self.closed: bool = False
        self.bind_args: tuple[str, int] | None = None
        self.listen_arg: int | None = None

        self.accept_return: tuple["MockSocket", tuple[str, int]] | None = None
        self.accept_exception: Exception | None = None

        self.recv_exception: Exception | None = None
        self.bind_exception: Exception | None = None

    def __enter__(self) -> "MockSocket":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def getpeername(self) -> tuple[str, int]:
        return self.peer_name

    def settimeout(self, value: float | None) -> None:
        self.timeout = value

    def setsockopt(self, level: int, optname: int, value: int | bytes) -> None:
        pass

    def recv(self, bufsize: int, flags: int = 0) -> bytes:
        if self.recv_exception:
            raise self.recv_exception
        if self.recv_data:
            return self.recv_data.pop(0)
        return b""

    def send(self, data: bytes, flags: int = 0) -> int:
        self.sent_data.append(data)
        return len(data)

    def sendall(self, data: bytes, flags: int = 0) -> None:
        self.sent_data.append(data)

    def close(self) -> None:
        self.closed = True

    def bind(self, address: tuple[str, int]) -> None:
        if self.bind_exception:
            raise self.bind_exception
        self.bind_args = address

    def listen(self, backlog: int) -> None:
        self.listen_arg = backlog

    def accept(self) -> tuple["MockSocket", tuple[str, int]]:
        if self.accept_exception:
            raise self.accept_exception
        if self.accept_return:
            return self.accept_return

        # Default mock behavior
        conn = MockSocket()
        return conn, ("127.0.0.1", 12345)
