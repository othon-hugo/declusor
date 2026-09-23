from unittest.mock import MagicMock

from declusor import contract


def test_session_context_initialization_and_properties() -> None:
    """SessionContext should properly hold and expose connection, console, and files."""
    connection = MagicMock(spec=contract.IConnection)
    console = MagicMock(spec=contract.IConsole)
    files = MagicMock(spec=contract.IClientFileStore)

    session = contract.SessionContext(
        connection=connection,
        console=console,
        files=files,
    )

    assert session.connection is connection
    assert session.console is console
    assert session.files is files


def test_session_context_execute_invokes_command_execute() -> None:
    """session.execute(command) must dispatch command.execute(session)."""
    connection = MagicMock(spec=contract.IConnection)
    console = MagicMock(spec=contract.IConsole)
    files = MagicMock(spec=contract.IClientFileStore)

    session = contract.SessionContext(
        connection=connection,
        console=console,
        files=files,
    )

    mock_command = MagicMock(spec=contract.ICommand)
    session.execute(mock_command)

    mock_command.execute.assert_called_once_with(session)


def test_session_context_backward_compatibility_tuple_unpacking() -> None:
    """SessionContext must support tuple indexing, unpacking, and len for backward compatibility."""
    connection = MagicMock(spec=contract.IConnection)
    console = MagicMock(spec=contract.IConsole)
    files = MagicMock(spec=contract.IClientFileStore)

    session = contract.SessionContext(
        connection=connection,
        console=console,
        files=files,
    )

    assert len(session) == 3
    assert session[0] is connection
    assert session[1] is console
    assert session[2] is files

    unpacked_conn, unpacked_console, unpacked_files = session
    assert unpacked_conn is connection
    assert unpacked_console is console
    assert unpacked_files is files


def test_controller_dependencies_alias() -> None:
    """ControllerDependencies must be an alias for SessionContext."""
    assert contract.ControllerDependencies is contract.SessionContext
