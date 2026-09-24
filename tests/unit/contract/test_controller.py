"""Unit tests for Controller types and dependency unpacking."""

from declusor import contract
from declusor.testing import DummyClientFileStore, DummyConnection, DummyConsole


def test_controller_dependencies_extract_order(
    dummy_connection: DummyConnection,
    dummy_console: DummyConsole,
    dummy_file_store: DummyClientFileStore,
) -> None:
    """ControllerDependencies unpacking order must preserve connection, console, files."""
    deps = contract.ControllerDependencies(dummy_connection, dummy_console, dummy_file_store)

    conn_out, console_out, files_out = deps
    assert conn_out is dummy_connection
    assert console_out is dummy_console
    assert files_out is dummy_file_store
