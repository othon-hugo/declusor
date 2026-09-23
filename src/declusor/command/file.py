from pathlib import Path
from typing import ClassVar

from declusor import config, contract, util
from declusor.command.dto import ExecuteFileDTO, UploadFileDTO


class _BaseFileCommand(contract.ICommand):
    """Abstract base class for operations that encode a local file for remote client invocation.

    Reads a local file, converts its content to Base64, formats a client-specific
    shell execution payload using the active client profile's operation template,
    transmits it, and streams the output to the console.

    Subclasses must define ``_OPCODE`` to specify the intended operation code.
    """

    _OPCODE: ClassVar[config.OperationCode] = NotImplemented  # type: ignore[assignment]

    def __init__(self, dto: ExecuteFileDTO | UploadFileDTO) -> None:
        """Initialize the base file command.

        Args:
            dto: Validated DTO containing the local file path.

        Raises:
            NotImplementedError: If a subclass does not define ``_OPCODE``.
        """

        super().__init__()

        if self._OPCODE is NotImplemented:
            raise NotImplementedError("_OPCODE must be defined by concrete subclasses.")

        self._dto = dto
        self._filepath: Path = dto.filepath

    @property
    def filepath(self) -> Path:
        """The validated path to the local file."""

        return self._filepath

    def send_request(self, session: contract.SessionContext) -> None:
        """Encode the local file and send the formatted operation command to the client.

        Args:
            session: Active session context providing client profile and connection transport.

        Raises:
            InvalidOperation: If the client profile cannot render the operation command.
            ConnectionClosed: If the connection is closed.
            ConnectionWriteError: If the socket write operation fails.
        """

        command_bytes = self._format_command(session)
        session.connection.write(command_bytes)

    def read_response(self, session: contract.SessionContext) -> None:
        """Read output chunks from the remote client and write them to the console.

        Args:
            session: Active session context providing connection and console interfaces.

        Raises:
            ConnectionClosed: If the remote peer terminates the connection unexpectedly.
        """

        for data in session.connection.read():
            session.console.write_binary_data(data)

    def _format_command(self, session: contract.SessionContext) -> bytes:
        """Format the file content into an encoded remote client command.

        Args:
            session: Active session providing client profile configuration.

        Returns:
            Encoded bytes ready for network transmission.

        Raises:
            InvalidOperation: If the client runtime fails to produce a valid command.
        """

        file_content = util.load_file(self._filepath)
        file_base64 = util.convert_to_base64(file_content)

        script_data = session.connection.client.render_operation_command(
            self._OPCODE,
            file_base64,
        )

        if not script_data:
            raise config.InvalidOperation("Failed to generate script data for the file operation.")

        return script_data.encode()


class ExecuteFile(_BaseFileCommand):
    """Upload and execute a local script file on the remote client.

    Encapsulates script execution by reading the local file defined in
    ``ExecuteFileDTO``, encoding it, generating the client-side execution
    command (using ``EXEC_FILE`` opcode), and streaming execution output.
    """

    _OPCODE: ClassVar[config.OperationCode] = config.OperationCode.EXEC_FILE

    def __init__(self, dto: ExecuteFileDTO) -> None:
        """Initialize ExecuteFile with validated parameters.

        Args:
            dto: Validated DTO containing the script file path.
        """

        super().__init__(dto=dto)


class UploadFile(_BaseFileCommand):
    """Upload and store a local file on the remote client without executing it.

    Encapsulates file transfer by reading the local file defined in
    ``UploadFileDTO``, encoding it, and instructing the client to store it
    locally using the ``STORE_FILE`` opcode.
    """

    _OPCODE: ClassVar[config.OperationCode] = config.OperationCode.STORE_FILE

    def __init__(self, dto: UploadFileDTO) -> None:
        """Initialize UploadFile with validated parameters.

        Args:
            dto: Validated DTO containing the file path to upload.
        """

        super().__init__(dto=dto)
