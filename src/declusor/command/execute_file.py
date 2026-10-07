from dataclasses import dataclass
from pathlib import Path

from declusor import config, util

from .base import BaseFileCommand


@dataclass(frozen=True)
class ExecuteFileDTO:
    """Data transfer object containing parameters for remote script execution.

    Encapsulates and validates the path to a local script file to be encoded,
    uploaded, and executed on the remote client.

    Raises:
        CommandValidationError: If the file path is empty or contains null bytes.
        StorageValidationError: If the file does not exist or is not a regular file.
    """

    filepath: Path | str
    """Validated, absolute or relative ``Path`` to an existing local file."""

    def __post_init__(self) -> None:
        raw_path = str(self.filepath).strip()

        if not raw_path:
            raise config.CommandValidationError("File path cannot be empty.", field="filepath", value=self.filepath)

        if "\0" in raw_path:
            raise config.CommandValidationError("File path cannot contain null bytes.", field="filepath", value=self.filepath)

        validated_path = util.ensure_file_exists(Path(self.filepath))
        object.__setattr__(self, "filepath", validated_path)


class ExecuteFile(BaseFileCommand[ExecuteFileDTO]):
    """Upload and execute a local script file on the remote client.

    Encapsulates script execution by reading the local file defined in
    ``ExecuteFileDTO``, encoding it, generating the client-side execution
    command (using ``EXEC_FILE`` opcode), and streaming execution output.
    """

    def __init__(self, dto: ExecuteFileDTO, /) -> None:
        """Initialize ExecuteFile with validated parameters.

        Args:
            dto: Validated DTO containing the script file path.
        """

        super().__init__(dto, opcode=config.OperationCode.EXEC_FILE)
