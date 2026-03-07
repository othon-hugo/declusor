from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from declusor import interface


def handle_command(cmd: "interface.ICommand", session: "interface.IConnection", console: "interface.IConsole") -> None:
    """Execute a command and stream the response to the console.

    This is the common pattern shared across file-based controllers:
    send the command, then read and display the response chunks.

    Args:
        cmd: The command to execute.
        session: The active connection.
        console: The console for output.
    """

    cmd.execute(session, console)

    for data in session.read():
        console.write_binary_data(data)
