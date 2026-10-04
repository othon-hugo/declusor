from collections.abc import Generator

import pytest

from declusor import contract
from declusor.testing import DummyConnection, DummyOperationRenderer

# [Test Doubles]


class ConcreteConnection(contract.IConnection):
    """Minimal concrete implementation of IConnection for contract tests."""

    def __init__(
        self,
        connection: contract.IConnection | None = None,
        *,
        renderer: contract.IOperationRenderer | None = None,
    ) -> None:
        """Initialize concrete connection double."""

        super().__init__(connection)
        self._renderer: contract.IOperationRenderer = renderer or DummyOperationRenderer()
        self._state: contract.ConnectionState = contract.ConnectionState.CREATED
        self._timeout: float | None = None
        self.is_closed: bool = False

    @property
    def state(self) -> contract.ConnectionState:
        """Return connection lifecycle state."""

        return self._state

    @property
    def renderer(self) -> contract.IOperationRenderer:
        """Return operation command renderer."""

        return self._renderer

    @property
    def timeout(self) -> float | None:
        """Return socket timeout in seconds."""

        return self._timeout

    @timeout.setter
    def timeout(self, value: float | None, /) -> None:
        """Set socket timeout in seconds."""

        self._timeout = value

    def read(self) -> Generator[bytes, None, None]:
        """Read framed bytes."""

        yield b""

    def write(self, content: bytes, /) -> None:
        """Transmit framed bytes."""

    def close(self) -> None:
        """Close connection resources."""

        self.is_closed = True
        self._state = contract.ConnectionState.CLOSED


# [Test Cases]


class TestConnectionState:
    """Test suite for ConnectionState lifecycle enum."""

    def test_connection_state_members__match_expected_str_values(self) -> None:
        """Verify ConnectionState enum members declare the expected string values."""

        from enum import StrEnum

        assert issubclass(contract.ConnectionState, StrEnum)
        assert contract.ConnectionState.CREATED.value == "CREATED"
        assert contract.ConnectionState.INITIALIZING.value == "INITIALIZING"
        assert contract.ConnectionState.CONNECTED.value == "CONNECTED"
        assert contract.ConnectionState.CLOSED.value == "CLOSED"
        assert len(contract.ConnectionState) == 4


class TestIOperationRenderer:
    """Test suite for IOperationRenderer and its IConnectionProfile alias."""

    def test_operation_renderer_direct_instantiation__raises_type_error(self) -> None:
        """Verify IOperationRenderer cannot be instantiated directly."""

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            contract.IOperationRenderer()  # type: ignore[abstract]

    def test_connection_profile_alias__points_to_operation_renderer(self) -> None:
        """Verify IConnectionProfile is an alias pointing to IOperationRenderer."""

        assert contract.IConnectionProfile is contract.IOperationRenderer

    def test_connection_profile_direct_instantiation__raises_type_error(self) -> None:
        """Verify IConnectionProfile cannot be instantiated directly."""

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            contract.IConnectionProfile()  # type: ignore[abstract]


class TestIConnection:
    """Test suite for IConnection base lifecycle contract."""

    def test_connection_direct_instantiation__raises_type_error(self) -> None:
        """Verify IConnection cannot be instantiated directly due to abstract methods."""

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            contract.IConnection()  # type: ignore[abstract]

    def test_connection_handshake_without_underlying__performs_no_action(self) -> None:
        """Verify handshake is a no-op when no underlying connection is configured."""

        connection = ConcreteConnection(None)

        connection.handshake()

        assert connection.state == contract.ConnectionState.CREATED

    def test_connection_handshake_with_underlying__delegates_to_underlying_connection(self) -> None:
        """Verify handshake delegates to underlying connection when present."""

        underlying = DummyConnection(initial_state=contract.ConnectionState.CREATED)
        connection = ConcreteConnection(underlying)

        assert underlying.initialize_called is False

        connection.handshake()

        assert underlying.initialize_called is True
        assert underlying.state == contract.ConnectionState.CONNECTED

    def test_connection_profile_property__returns_renderer_instance(self) -> None:
        """Verify profile property alias returns the renderer instance."""

        renderer = DummyOperationRenderer()
        connection = ConcreteConnection(renderer=renderer)

        assert connection.profile is renderer
        assert connection.profile is connection.renderer

    def test_connection_context_manager_scope__returns_self_and_closes_on_exit(self) -> None:
        """Verify context manager protocol returns self and automatically invokes close on exit."""

        connection = ConcreteConnection()

        with connection as active_connection:
            assert active_connection is connection
            assert active_connection.is_closed is False

        assert connection.is_closed is True
        assert connection.state == contract.ConnectionState.CLOSED

    def test_connection_context_manager_scope__exception_raised__closes_on_exit(self) -> None:
        """Verify context manager protocol guarantees invoking close even when exception is raised."""

        connection = ConcreteConnection()

        with pytest.raises(RuntimeError, match="network error"):
            with connection:
                raise RuntimeError("network error")

        assert connection.is_closed is True
        assert connection.state == contract.ConnectionState.CLOSED

    def test_connection_timeout__getter_and_setter__updates_timeout(self) -> None:
        """Verify timeout setter mutates timeout property and accepts float or None."""

        connection = ConcreteConnection()

        assert connection.timeout is None

        connection.timeout = 5.5
        assert connection.timeout == 5.5

        connection.timeout = None
        assert connection.timeout is None
