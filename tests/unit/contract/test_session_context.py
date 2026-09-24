"""Unit tests for SessionContext coordination and backward-compatible interface."""

from declusor import contract
from tests.testing import (
    DummyClientFileStore,
    DummyCommand,
    DummyConnection,
    DummyConsole,
)


def test_session_context_initialization_and_properties(
    dummy_connection: DummyConnection,
    dummy_console: DummyConsole,
    dummy_file_store: DummyClientFileStore,
) -> None:
    """SessionContext should properly hold and expose connection, console, and files."""
    session = contract.SessionContext(
        connection=dummy_connection,
        console=dummy_console,
        files=dummy_file_store,
    )

    assert session.connection is dummy_connection
    assert session.console is dummy_console
    assert session.files is dummy_file_store


def test_session_context_execute_invokes_command_execute(
    test_session: contract.SessionContext,
) -> None:
    """session.execute(command) must dispatch command.execute(session)."""
    command = DummyCommand()
    test_session.execute(command)

    assert command.call_sequence == ["send_request", "read_response"]


def test_session_context_backward_compatibility_tuple_unpacking(
    dummy_connection: DummyConnection,
    dummy_console: DummyConsole,
    dummy_file_store: DummyClientFileStore,
) -> None:
    """SessionContext must support tuple indexing, unpacking, and len for backward compatibility."""
    session = contract.SessionContext(
        connection=dummy_connection,
        console=dummy_console,
        files=dummy_file_store,
    )

    assert len(session) == 3
    assert session[0] is dummy_connection
    assert session[1] is dummy_console
    assert session[2] is dummy_file_store

    unpacked_conn, unpacked_console, unpacked_files = session
    assert unpacked_conn is dummy_connection
    assert unpacked_console is dummy_console
    assert unpacked_files is dummy_file_store


def test_controller_dependencies_alias() -> None:
    """ControllerDependencies must be an alias for SessionContext."""
    assert contract.ControllerDependencies is contract.SessionContext
