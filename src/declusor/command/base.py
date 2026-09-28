from typing import TYPE_CHECKING, Literal

from declusor import config, contract, util

if TYPE_CHECKING:
    from .execute_file import ExecuteFileDTO
    from .upload_file import UploadFileDTO


class BaseStreamCommand(contract.ICommand):
    """Base command for operations streaming binary chunks from client connection to view.

    Encapsulates the standard response loop that reads streamed output chunks from
    ``session.connection`` and forwards them directly to ``session.view.write_binary_data``.
    """

    def read_response(self, session: contract.SessionContext, /) -> None:
        """Stream response chunks from the remote client and write them to the view.

        Args:
            session: Active session context providing connection and view interfaces.

        Raises:
            ConnectionClosed: If the remote peer terminates the connection unexpectedly.
        """

        for data in session.connection.read():
            session.view.write_binary_data(data)


class BaseFileCommand[T: "ExecuteFileDTO | UploadFileDTO"](BaseStreamCommand):
    """Abstract base class for operations that encode a local file for remote client invocation.

    Reads a local file, converts its content to Base64, formats a client-specific
    shell execution payload using the active client profile's operation template,
    transmits it, and streams the output to the console.
    """

    _SupportedOperationCodes = Literal[
        config.OperationCode.EXEC_FILE,
        config.OperationCode.STORE_FILE,
    ]

    def __init__(self, dto: T, opcode: "_SupportedOperationCodes") -> None:
        """Initialize the base file command.

        Args:
            dto: Validated DTO containing the local file path.
            opcode: Operational code defining the target client operation.
        """

        super().__init__()

        self._dto: T = dto
        self._opcode: BaseFileCommand._SupportedOperationCodes = opcode

    @property
    def dto(self) -> T:
        """The command parameters."""

        return self._dto

    @property
    def opcode(self) -> "_SupportedOperationCodes":
        """The operational code for this file command."""

        return self._opcode

    def send_request(self, session: contract.SessionContext, /) -> None:
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

    def _format_command(self, session: contract.SessionContext) -> bytes:
        """Format the file content into an encoded remote client command.

        Args:
            session: Active session providing client profile configuration.

        Returns:
            Encoded bytes ready for network transmission.

        Raises:
            InvalidOperation: If the client runtime fails to produce a valid command.
        """

        file_content = util.load_file(self._dto.filepath)
        file_base64 = util.convert_to_base64(file_content)

        script_data = session.connection.profile.render_operation_command(
            self._opcode,
            file_base64,
        )

        if not script_data:
            raise config.InvalidOperation("Failed to generate script data for the file operation.")

        return script_data.encode()
