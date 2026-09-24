from collections.abc import Generator

import pytest

from declusor import contract
from declusor.testing.doubles import (
    DummyApplication,
    DummyConnection,
    DummyConnectionProfile,
    DummyConsole,
    DummyPlugin,
    DummyPluginFileStore,
    DummyPluginRuntime,
    DummyRouter,
    DummySocket,
)
from declusor.testing.factories import (
    create_dummy_plugin_config,
    create_test_session,
)


@pytest.fixture
def dummy_console() -> DummyConsole:
    """Provide a fresh in-memory DummyConsole."""

    return DummyConsole()


@pytest.fixture
def dummy_profile() -> DummyConnectionProfile:
    """Provide a fresh DummyConnectionProfile."""

    return DummyConnectionProfile()


@pytest.fixture
def dummy_connection(dummy_profile: DummyConnectionProfile) -> DummyConnection:
    """Provide a fresh DummyConnection backed by dummy_profile."""

    return DummyConnection(client=dummy_profile)


@pytest.fixture
def dummy_file_store() -> DummyPluginFileStore:
    """Provide a fresh DummyPluginFileStore."""

    return DummyPluginFileStore()


@pytest.fixture
def test_session(
    dummy_connection: DummyConnection,
    dummy_console: DummyConsole,
    dummy_file_store: DummyPluginFileStore,
) -> contract.SessionContext:
    """Provide a SessionContext wired to isolated test doubles."""

    return create_test_session(
        connection=dummy_connection,
        console=dummy_console,
        files=dummy_file_store,
    )


@pytest.fixture
def dummy_runtime(dummy_file_store: DummyPluginFileStore) -> DummyPluginRuntime:
    """Provide a fresh DummyPluginRuntime."""

    return DummyPluginRuntime(file_store=dummy_file_store)


@pytest.fixture
def dummy_plugin() -> Generator[type[DummyPlugin], None, None]:
    """Provide a clean DummyPlugin class with isolated static state."""

    DummyPlugin.reset()
    yield DummyPlugin
    DummyPlugin.reset()


@pytest.fixture
def dummy_router() -> DummyRouter:
    """Provide a fresh DummyRouter."""

    return DummyRouter()


@pytest.fixture
def dummy_socket() -> DummySocket:
    """Provide a fresh DummySocket."""

    return DummySocket()


@pytest.fixture
def dummy_plugin_config() -> contract.PluginConfig:
    """Provide a standard test PluginConfig."""

    return create_dummy_plugin_config()


dummy_plugin_config = dummy_plugin_config


@pytest.fixture
def dummy_app() -> DummyApplication:
    """Provide a fresh DummyApplication."""

    return DummyApplication()
