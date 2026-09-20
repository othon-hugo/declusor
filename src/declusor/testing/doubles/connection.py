from collections.abc import Generator, Sequence
from typing import Self

from declusor import config, contract
from declusor.testing.doubles.profile import DummyConnectionProfile


class DummyConnection(contract.IConnection):
    """Fully-typed test double for active client network connections."""

    def __init__(
        self,
        client: contract.IConnectionProfile | None = None,
        incoming_chunks: Sequence[bytes] | None = None,
        initial_state: contract.ConnectionState = contract.ConnectionState.CONNECTED,
    ) -> None:
        self._client: contract.IConnectionProfile = client or DummyConnectionProfile()
        self._state: contract.ConnectionState = initial_state
        self._timeout: float | None = None
        self.written: list[bytes] = []
        self.incoming_chunks: list[bytes] = list(incoming_chunks) if incoming_chunks is not None else [b"chunk1\n", b"chunk2\n"]
        self.initialize_called: bool = False
        self.closed: bool = False
        self.initialize_error: BaseException | None = None
        self.write_error: BaseException | None = None
        self.read_error: BaseException | None = None

    @property
    def state(self) -> contract.ConnectionState:
        return self._state

    @state.setter
    def state(self, value: contract.ConnectionState) -> None:
        self._state = value

    @property
    def profile(self) -> contract.IConnectionProfile:
        return self._client

    @property
    def timeout(self) -> float | None:
        return self._timeout

    @timeout.setter
    def timeout(self, value: float | None, /) -> None:
        self._timeout = value

    def initialize(self) -> None:
        """Simulate protocol handshake."""

        self.initialize_called = True

        if self._state == contract.ConnectionState.CLOSED:
            raise config.ConnectionError("Cannot initialize a closed connection.")

        if self.initialize_error is not None:
            raise self.initialize_error

        self._state = contract.ConnectionState.CONNECTED

    def read(self) -> Generator[bytes, None, None]:
        """Yield simulated incoming bytes chunks."""

        if self.read_error is not None:
            raise self.read_error

        yield from self.incoming_chunks

    def write(self, content: bytes, /) -> None:
        """Record transmitted bytes."""

        if self._state != contract.ConnectionState.CONNECTED:
            raise config.ConnectionError("Connection is not open.")

        if self.write_error is not None:
            raise self.write_error

        self.written.append(content)

    def close(self) -> None:
        """Simulate closing transport resources."""

        self.closed = True
        self._state = contract.ConnectionState.CLOSED

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        self.close()
