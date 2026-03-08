from pathlib import Path

from declusor import config, interface, util


class _BaseFileCommand(interface.ICommand):
    """Shared logic for commands that base64-encode a local file and invoke a client function.

    Subclasses set ``_OPCODE`` to select the appropriate client-side function
    (e.g. ``EXEC_FILE`` → ``execute_base64_encoded_value``).
    """

    _OPCODE: config.OperationCode = NotImplemented

    def __init__(self, filepath: str | Path) -> None:
        """Resolve and validate *filepath* before storing it.

        Args:
            filepath: Path to the local file to operate on.

        Raises:
            NotImplementedError: If ``_OPCODE`` was not overridden by a subclass.
            InvalidOperation: If the file does not exist or is not a regular file.
        """

        if self._OPCODE == NotImplemented:
            raise NotImplementedError("FUNC_NAME must be defined in subclasses.")

        self._filepath = util.ensure_file_exists(filepath)

    def execute(self, connection: interface.IConnection, console: interface.IConsole, /) -> None:
        """Serialize and transmit the file to the remote client.

        Reads the file, base64-encodes it, wraps it in the appropriate
        client shell command, and writes the result to *session*.

        Args:
            connection: The active connection to write the command to.
            console: Unused; present to satisfy the ``ICommand`` interface.

        Raises:
            InvalidOperation: If the profile does not support the opcode.
        """

        connection.write(self._format_command(connection.client))

    def _format_command(self, profile: interface.IConnectionProfile) -> bytes:
        """Build the encoded command bytes using *profile*'s operation mapping.

        Base64-encodes the file content, then passes it to
        ``profile.format_operation_script`` to produce the shell invocation.

        Args:
            profile: The client profile providing the operation-to-function mapping.

        Returns:
            UTF-8-encoded shell command string ready for transmission.

        Raises:
            InvalidOperation: If the profile returns ``None`` for ``_OPCODE``.
        """

        file_content = util.load_file(self._filepath)
        file_base64 = util.convert_to_base64(file_content)

        script_data = profile.render_operation_command(self._OPCODE, file_base64)

        if not script_data:
            raise config.InvalidOperation("Failed to generate script data for the file operation.")

        return script_data.encode()


class ExecuteFile(_BaseFileCommand):
    """Upload and execute a local script on the remote client."""

    _OPCODE = config.OperationCode.EXEC_FILE


class UploadFile(_BaseFileCommand):
    """Upload a local file to the remote client without executing it."""

    _OPCODE = config.OperationCode.STORE_FILE
