from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from declusor import config, contract, util
from declusor.command.base import BaseStreamCommand


@dataclass(frozen=True)
class ExecuteFileDTO:
    """Data transfer object containing parameters for remote script execution.

    Encapsulates and validates the path to a local script file to be encoded,
    uploaded, and executed on the remote client.

    Attributes:
        filepath: Validated, absolute or relative ``Path`` to an existing local file.

    Raises:
        InvalidOperation: If the specified file does not exist or is not a regular file.
    """

    filepath: Path

    def __init__(self, filepath: str | Path) -> None:
        path_obj = Path(filepath)
        validated_path = util.ensure_file_exists(path_obj)

        object.__setattr__(self, "filepath", validated_path)


@dataclass(frozen=True)
class UploadFileDTO:
    """Data transfer object containing parameters for file upload.

    Encapsulates and validates the path to a local file to be uploaded and stored
    on the remote client without execution.

    Attributes:
        filepath: Validated ``Path`` to an existing local file.

    Raises:
        InvalidOperation: If the specified file does not exist or is not a regular file.
    """

    filepath: Path

    def __init__(self, filepath: str | Path) -> None:
        path_obj = Path(filepath)
        validated_path = util.ensure_file_exists(path_obj)

        object.__setattr__(self, "filepath", validated_path)


class BaseFileCommand[T: ExecuteFileDTO | UploadFileDTO](BaseStreamCommand):
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


class ExecuteFile(BaseFileCommand[ExecuteFileDTO]):
    """Upload and execute a local script file on the remote client.

    Encapsulates script execution by reading the local file defined in
    ``ExecuteFileDTO``, encoding it, generating the client-side execution
    command (using ``EXEC_FILE`` opcode), and streaming execution output.
    """

    def __init__(self, dto: ExecuteFileDTO) -> None:
        """Initialize ExecuteFile with validated parameters.

        Args:
            dto: Validated DTO containing the script file path.
        """

        super().__init__(dto=dto, opcode=config.OperationCode.EXEC_FILE)


class UploadFile(BaseFileCommand[UploadFileDTO]):
    """Upload and store a local file on the remote client without executing it.

    Encapsulates file transfer by reading the local file defined in
    ``UploadFileDTO``, encoding it, and instructing the client to store it
    locally using the ``STORE_FILE`` opcode.
    """

    def __init__(self, dto: UploadFileDTO) -> None:
        """Initialize UploadFile with validated parameters.

        Args:
            dto: Validated DTO containing the file path to upload.
        """

        super().__init__(dto=dto, opcode=config.OperationCode.STORE_FILE)
