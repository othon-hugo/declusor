from collections.abc import Generator

import pytest

from declusor import contract
from declusor.testing import doubles

from .factories import (
    create_dummy_plugin_config,
    create_test_session,
)


@pytest.fixture
def dummy_view() -> doubles.DummyView:
    """Provide a fresh in-memory doubles.DummyView."""

    return doubles.DummyView()


@pytest.fixture
def dummy_input_source() -> doubles.DummyInputSource:
    """Provide a fresh in-memory doubles.DummyInputSource."""

    return doubles.DummyInputSource()


@pytest.fixture
def dummy_renderer() -> doubles.DummyOperationRenderer:
    """Provide a fresh doubles.DummyOperationRenderer."""

    return doubles.DummyOperationRenderer()


@pytest.fixture
def dummy_connection(dummy_renderer: doubles.DummyOperationRenderer) -> doubles.DummyConnection:
    """Provide a fresh doubles.DummyConnection backed by dummy_renderer."""

    return doubles.DummyConnection(client=dummy_renderer, initial_state=contract.ConnectionState.CONNECTED)


@pytest.fixture
def dummy_file_store() -> doubles.DummyPluginFileStore:
    """Provide a fresh doubles.DummyPluginFileStore."""

    return doubles.DummyPluginFileStore()


@pytest.fixture
def test_session(
    dummy_connection: doubles.DummyConnection,
    dummy_view: doubles.DummyView,
    dummy_input_source: doubles.DummyInputSource,
    dummy_file_store: doubles.DummyPluginFileStore,
) -> contract.SessionContext:
    """Provide a SessionContext wired to isolated test doubles."""

    return create_test_session(
        connection=dummy_connection,
        view=dummy_view,
        input_source=dummy_input_source,
        files=dummy_file_store,
    )


@pytest.fixture
def dummy_runtime(dummy_file_store: doubles.DummyPluginFileStore) -> doubles.DummyPluginRuntime:
    """Provide a fresh doubles.DummyPluginRuntime."""

    return doubles.DummyPluginRuntime(file_store=dummy_file_store)


@pytest.fixture
def dummy_plugin() -> Generator[type[doubles.DummyPlugin], None, None]:
    """Provide a clean doubles.DummyPlugin class with isolated static state."""

    doubles.DummyPlugin.reset()
    yield doubles.DummyPlugin
    doubles.DummyPlugin.reset()


@pytest.fixture
def dummy_router() -> doubles.DummyRouter:
    """Provide a fresh doubles.DummyRouter."""

    return doubles.DummyRouter()


@pytest.fixture
def dummy_socket() -> doubles.DummySocket:
    """Provide a fresh doubles.DummySocket."""

    return doubles.DummySocket()


@pytest.fixture
def dummy_plugin_config() -> contract.PluginConfig[contract.ParsedArguments]:
    """Provide a standard test PluginConfig."""

    return create_dummy_plugin_config()


@pytest.fixture
def dummy_transport() -> doubles.DummyTransport:
    """Provide a fresh doubles.DummyTransport."""

    return doubles.DummyTransport()


@pytest.fixture
def memory_transport_pair() -> tuple[doubles.MemoryTransport, doubles.MemoryTransport]:
    """Provide a linked pair of in-memory transports."""

    return doubles.create_memory_transport_pair()


@pytest.fixture
def memory_transport_listener() -> doubles.MemoryTransportListener:
    """Provide a fresh doubles.MemoryTransportListener."""

    return doubles.MemoryTransportListener()


@pytest.fixture
def dummy_session_runner() -> doubles.DummySessionRunner:
    """Provide a fresh doubles.DummySessionRunner."""

    return doubles.DummySessionRunner()


@pytest.fixture
def dummy_app() -> doubles.DummyApplication:
    """Provide a fresh doubles.DummyApplication with doubles.DummyPlugin registered."""

    declusor_app = doubles.DummyApplication()
    declusor_app.register_plugin(doubles.DummyPlugin)

    return declusor_app
