from pathlib import Path

from declusor import config, contract, util


class _BaseFileCommand(contract.ICommand):
    """Shared logic for commands that base64-encode a local file and invoke a client function.

    Subclasses set ``_OPCODE`` to select the appropriate client-side function
    (e.g. ``EXEC_FILE`` → ``execute_base64_encoded_value``).
    """

    _OPCODE: config.OperationCode = NotImplemented

    def __init__(
        self,
        connection: contract.IConnection,
        console: contract.IConsole,
        *,
        filepath: str | Path,
    ) -> None:
        super().__init__(connection=connection, console=console)

        if NotImplemented == self._OPCODE:
            raise NotImplementedError("FUNC_NAME must be defined in subclasses.")

        self._filepath = util.ensure_file_exists(filepath)

    def send_request(self) -> None:
        """[...]

        Raises:
            InvalidOperation: If the profile does not support the opcode.
        """

        self._connection.write(self._format_command())

    def read_response(self) -> None:
        """[...]

        Raises:
            InvalidOperation: If the profile does not support the opcode.
        """

        for data in self._connection.read():
            self._console.write_binary_data(data)

    def _format_command(self) -> bytes:
        """Build the encoded command bytes using *profile*'s operation mapping.

        Base64-encodes the file content, then passes it to
        ``profile.format_operation_script`` to produce the shell invocation.

        Returns:
            UTF-8-encoded shell command string ready for transmission.

        Raises:
            InvalidOperation: If the profile returns ``None`` for ``_OPCODE``.
        """

        file_content = util.load_file(self._filepath)
        file_base64 = util.convert_to_base64(file_content)

        script_data = self._connection.client.render_operation_command(self._OPCODE, file_base64)

        if not script_data:
            raise config.InvalidOperation("Failed to generate script data for the file operation.")

        return script_data.encode()


class ExecuteFile(_BaseFileCommand):
    """Upload and execute a local script on the remote client."""

    _OPCODE = config.OperationCode.EXEC_FILE


class UploadFile(_BaseFileCommand):
    """Upload a local file to the remote client without executing it."""

    _OPCODE = config.OperationCode.STORE_FILE
