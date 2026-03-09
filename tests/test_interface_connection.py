"""Tests for the ``declusor.interface.connection`` module."""

import pytest

from declusor import config
from declusor.interface import connection


# =============================================================================
# Dummies/Mocks
# =============================================================================

class DummyProfile(connection.IConnectionProfile):
    """Null-implementation subclass delegating attributes to the interface."""

    @property
    def default_buffer_size(self) -> int:
        return super().default_buffer_size

    @property
    def default_timeout(self) -> float | None:
        return super().default_timeout

    def iter_library_paths(self):
        super().iter_library_paths()
        yield from []

    def resolve_module_path(self, module_filename: str):
        return super().resolve_module_path(module_filename)

    def render_operation_command(self, opcode: config.OperationCode, *args: str):
        return super().render_operation_command(opcode, *args)

    def render_client_script(self, host: str, port: int):
        return super().render_client_script(host, port)


class DummyConnection(connection.IConnection):
    """Null-implementation subclass delegating IO ops to the base class."""

    @property
    def client(self) -> connection.IConnectionProfile:
        return super().client

    @property
    def timeout(self) -> float | None:
        return super().timeout

    @timeout.setter
    def timeout(self, value: float | None) -> None:
        super(DummyConnection, type(self)).timeout.fset(self, value)  # type: ignore

    def initialize(self) -> None:
        super().initialize()

    def read(self):
        super().read()
        yield b""

    def write(self, content: bytes) -> None:
        super().write(content)

    def close(self) -> None:
        super().close()


# =============================================================================
# Tests: IConnectionProfile (Interface contract)
# =============================================================================

def test_iconnectionprofile_properties_raise_not_implemented_error() -> None:
    """Accessing abstract properties on ``IConnectionProfile`` must raise a ``NotImplementedError``."""
    # ARRANGE: Profile instantiation
    profile = DummyProfile()

    # ACT & ASSERT: Catch expected exceptions on abstract attribute lookups
    with pytest.raises(NotImplementedError):
        _ = profile.default_buffer_size

    with pytest.raises(NotImplementedError):
        _ = profile.default_timeout

def test_iconnectionprofile_methods_raise_not_implemented_error() -> None:
    """Invoking abstract methods on ``IConnectionProfile`` must raise a ``NotImplementedError``."""
    # ARRANGE: Profile instantiation
    profile = DummyProfile()

    # ACT & ASSERT: Catch exceptions on explicit generic method dispatches
    with pytest.raises(NotImplementedError):
        list(profile.iter_library_paths())

    with pytest.raises(NotImplementedError):
        profile.resolve_module_path("example")

    with pytest.raises(NotImplementedError):
        profile.render_operation_command(config.OperationCode.EXEC_FILE)

    with pytest.raises(NotImplementedError):
        profile.render_client_script("127.0.0.1", 8080)


# =============================================================================
# Tests: IConnection (Interface contract)
# =============================================================================

def test_iconnection_properties_raise_not_implemented_error() -> None:
    """Accessing abstract properties on ``IConnection`` must raise a ``NotImplementedError``."""
    # ARRANGE: Dummy execution connection instance
    conn = DummyConnection()

    # ACT & ASSERT: Read attributes trigger defaults
    with pytest.raises(NotImplementedError):
        _ = conn.client

    with pytest.raises(NotImplementedError):
        _ = conn.timeout

    with pytest.raises(NotImplementedError):
        conn.timeout = 5.0

def test_iconnection_methods_raise_not_implemented_error() -> None:
    """Calling abstract communication lifecycle methods on ``IConnection`` must raise a ``NotImplementedError``."""
    # ARRANGE: Dummy network object
    conn = DummyConnection()

    # ACT & ASSERT: Fire method exceptions internally
    with pytest.raises(NotImplementedError):
        conn.initialize()

    with pytest.raises(NotImplementedError):
        list(conn.read())

    with pytest.raises(NotImplementedError):
        conn.write(b"")

    with pytest.raises(NotImplementedError):
        conn.close()

def test_iconnection_context_manager_delegates_to_close() -> None:
    """Using an ``IConnection`` as a context manager must successfully dispatch a ``close`` operation on exit."""
    # ARRANGE: Trace call path of generic close context
    close_called = False

    class SubConnection(DummyConnection):
        def close(self) -> None:
            nonlocal close_called
            close_called = True

    conn = SubConnection()

    # ACT: Run loop explicitly resolving context setup and teardown
    with conn as c:
        assert c is conn
        assert not close_called

    # ASSERT: Exit teardown fired safely
    assert close_called is True
