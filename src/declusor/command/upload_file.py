from dataclasses import dataclass
from pathlib import Path

from declusor import config, util
from declusor.command.base import BaseFileCommand


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

        super().__init__(dto, opcode=config.OperationCode.STORE_FILE)
