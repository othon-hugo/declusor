"""Deterministic connection test double managing state transitions."""

from collections.abc import Generator, Sequence
from typing import Self

from declusor import contract

from .profile import DummyOperationRenderer


class DummyConnection(contract.IConnection):
    """Fully-typed test double for active client network connections."""

    def __init__(
        self,
        client: contract.IOperationRenderer | None = None,
        incoming_chunks: Sequence[bytes] | None = None,
        initial_state: contract.ConnectionState = contract.ConnectionState.CREATED,
        transport: contract.ITransport | None = None,
    ) -> None:
        """Initialize connection double with client renderer, incoming chunks, and state."""

        self._client: contract.IOperationRenderer = client or DummyOperationRenderer()
        self._state: contract.ConnectionState = initial_state
        self._timeout: float | None = None
        self._transport: contract.ITransport | None = transport
        self.written: list[bytes] = []
        self.incoming_chunks: list[bytes] = list(incoming_chunks) if incoming_chunks is not None else [b"chunk1\n", b"chunk2\n"]
        self.initialize_called: bool = False
        self.closed: bool = False
        self.initialize_error: BaseException | None = None
        self.write_error: BaseException | None = None
        self.read_error: BaseException | None = None

    @property
    def state(self) -> contract.ConnectionState:
        """Return the current connection state."""

        return self._state

    @state.setter
    def state(self, value: contract.ConnectionState) -> None:
        """Update connection state."""

        self._state = value

    @property
    def renderer(self) -> contract.IOperationRenderer:
        """Return the active operation renderer."""

        return self._client

    @property
    def timeout(self) -> float | None:
        """Return the connection timeout in seconds."""

        return self._timeout

    @timeout.setter
    def timeout(self, value: float | None, /) -> None:
        """Set connection timeout in seconds."""

        self._timeout = value

    def handshake(self) -> None:
        """Simulate protocol handshake."""

        self.ensure_can_handshake()
        self.initialize_called = True

        if self.initialize_error is not None:
            raise self.initialize_error

        self._state = contract.ConnectionState.CONNECTED

    def read(self) -> Generator[bytes, None, None]:
        """Yield simulated incoming bytes chunks."""

        self.ensure_can_perform_io()

        if self.read_error is not None:
            raise self.read_error

        yield from self.incoming_chunks

    def write(self, content: bytes, /) -> None:
        """Record transmitted bytes."""

        self.ensure_can_perform_io()

        if self.write_error is not None:
            raise self.write_error

        self.written.append(content)
        if self._transport is not None:
            self._transport.write(content)

    def close(self) -> None:
        """Simulate closing transport resources."""

        if self.is_closed:
            return

        self.closed = True
        self._state = contract.ConnectionState.CLOSED
        if self._transport is not None:
            self._transport.close()

    def __enter__(self) -> Self:
        """Enter context manager, returning self."""

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context manager, closing simulated connection."""

        self.close()
