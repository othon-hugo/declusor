from pathlib import Path

from declusor import config, interface, util


class _BaseFileCommand(interface.ICommand):
    """Base command for file operations (execution or upload)."""

    _OPCODE: config.OperationCode = NotImplemented

    def __init__(self, filepath: str | Path) -> None:
        """
        Initialize the file command.

        Args:
            filepath: Path to the file to operate on.
            language: The language of the target environment.
        """

        if self._OPCODE == NotImplemented:
            raise NotImplementedError("FUNC_NAME must be defined in subclasses.")

        self._filepath = util.ensure_file_exists(filepath)

    def execute(self, session: interface.IConnection, console: interface.IConsole, /) -> None:
        """Execute the command on the session.

        Args:
            session: The active session.
        """

        session.write(self._format_command(session.client))

    def _format_command(self, profile: interface.IProfile) -> bytes:
        """Generate the encoded command bytes to send to the target.

        Returns:
            The base64 encoded command string ready for transmission.
        """

        file_content = util.load_file(self._filepath)
        file_base64 = util.convert_to_base64(file_content)

        script_data = profile.format_operation_script(self._OPCODE, file_base64)

        if not script_data:
            raise config.InvalidOperation("Failed to generate script data for the file operation.")

        return script_data.encode()


class ExecuteFile(_BaseFileCommand):
    """Command to upload and execute a file on the target machine."""

    _OPCODE = config.OperationCode.EXEC_FILE


class UploadFile(_BaseFileCommand):
    """Command to upload a file to the target machine."""

    _OPCODE = config.OperationCode.STORE_FILE
