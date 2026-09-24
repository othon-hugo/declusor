from unittest.mock import MagicMock

from declusor import contract


def test_controller_dependencies_extract_order() -> None:
    """ControllerDependencies unpacking order must preserve connection, console, files."""

    connection = MagicMock(spec=contract.IConnection)
    console = MagicMock(spec=contract.IConsole)
    files = MagicMock(spec=contract.IClientFileStore)

    deps = contract.ControllerDependencies(connection, console, files)

    conn_out, console_out, files_out = deps
    assert conn_out is connection
    assert console_out is console
    assert files_out is files
