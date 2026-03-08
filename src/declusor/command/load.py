from pathlib import Path

from declusor import config, interface, util


class LoadPayload(interface.ICommand):
    """Send a pre-built payload file verbatim to the remote client.

    Unlike ``ExecuteFile``, the file is not base64-encoded; it is sent as raw
    bytes. Intended for payloads already formatted for direct execution by the
    client runtime.
    """

    def __init__(self, filepath: str | Path) -> None:
        """Resolve and validate *filepath*.

        Args:
            filepath: Path to the payload file to send.

        Raises:
            InvalidOperation: If the file does not exist or is not a regular file.
        """

        self._filepath = util.ensure_file_exists(filepath)

    def execute(self, session: interface.IConnection, console: interface.IConsole, /) -> None:
        """Read and transmit the payload file to the remote client.

        Args:
            session: The active connection to write the payload to.
            console: Unused; present to satisfy the ``ICommand`` interface.

        Raises:
            InvalidOperation: If the file content cannot be read.
        """

        if (file_content := util.try_load_file(self._filepath)) is None:
            raise config.InvalidOperation(f"failed to load file content: {self._filepath!r}")

        session.write(file_content)
