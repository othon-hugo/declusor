from dataclasses import dataclass
from pathlib import Path

from declusor import config, util
from declusor.command.base import BaseFileCommand


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
