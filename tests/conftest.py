"""Root pytest configuration and typed fixtures for Declusor test suite."""

from collections.abc import Generator

import pytest

from declusor import contract
from tests.testing import (
    DummyApplication,
    DummyClientFileStore,
    DummyClientPlugin,
    DummyClientRuntime,
    DummyConnection,
    DummyConnectionProfile,
    DummyConsole,
    DummyRouter,
    DummySocket,
    create_dummy_client_config,
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
def dummy_file_store() -> DummyClientFileStore:
    """Provide a fresh DummyClientFileStore."""
    return DummyClientFileStore()


@pytest.fixture
def test_session(
    dummy_connection: DummyConnection,
    dummy_console: DummyConsole,
    dummy_file_store: DummyClientFileStore,
) -> contract.SessionContext:
    """Provide a SessionContext wired to isolated test doubles."""
    return create_test_session(
        connection=dummy_connection,
        console=dummy_console,
        files=dummy_file_store,
    )


@pytest.fixture
def dummy_runtime(dummy_file_store: DummyClientFileStore) -> DummyClientRuntime:
    """Provide a fresh DummyClientRuntime."""
    return DummyClientRuntime(file_store=dummy_file_store)


@pytest.fixture
def dummy_plugin() -> Generator[type[DummyClientPlugin], None, None]:
    """Provide a clean DummyClientPlugin class with isolated static state."""
    DummyClientPlugin.reset()
    yield DummyClientPlugin
    DummyClientPlugin.reset()


@pytest.fixture
def dummy_router() -> DummyRouter:
    """Provide a fresh DummyRouter."""
    return DummyRouter()


@pytest.fixture
def dummy_socket() -> DummySocket:
    """Provide a fresh DummySocket."""
    return DummySocket()


@pytest.fixture
def dummy_client_config() -> contract.ClientConfig:
    """Provide a standard test ClientConfig."""
    return create_dummy_client_config()


@pytest.fixture
def dummy_app() -> DummyApplication:
    """Provide a fresh DummyApplication."""
    return DummyApplication()
