"""Test support package defining reusable, fully-typed test doubles and fixtures."""

from tests.testing.doubles import (
    DummyClientFileStore,
    DummyClientPlugin,
    DummyClientRuntime,
    DummyCommand,
    DummyConnection,
    DummyConnectionProfile,
    DummyConsole,
    DummyRouter,
    DummySocket,
)
from tests.testing.factories import (
    create_dummy_client_config,
    create_dummy_controller_request,
    create_test_session,
)

__all__ = [
    "DummyClientFileStore",
    "DummyClientPlugin",
    "DummyClientRuntime",
    "DummyCommand",
    "DummyConnection",
    "DummyConnectionProfile",
    "DummyConsole",
    "DummyRouter",
    "DummySocket",
    "create_dummy_client_config",
    "create_dummy_controller_request",
    "create_test_session",
]
