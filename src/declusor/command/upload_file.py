from dataclasses import dataclass
from pathlib import Path

from declusor import config, util

from .base import BaseFileCommand


@dataclass(frozen=True)
class UploadFileDTO:
    """Data transfer object containing parameters for file upload.

    Encapsulates and validates the path to a local file to be uploaded and stored
    on the remote client without execution, along with an optional remote destination path.

    Raises:
        InvalidOperation: If the local file does not exist, is not a regular file,
            or if paths are empty, contain null bytes, or contain control characters.
    """

    filepath: Path | str
    """Validated, absolute or relative ``Path`` to an existing local file."""

    destination: str | None = None
    """Optional remote destination file path."""

    def __post_init__(self) -> None:
        raw_path = str(self.filepath).strip()
        if not raw_path:
            raise config.CommandValidationError("File path cannot be empty.", field="filepath", value=self.filepath)

        if "\0" in raw_path:
            raise config.CommandValidationError("File path cannot contain null bytes.", field="filepath", value=self.filepath)

        validated_path = util.ensure_file_exists(Path(self.filepath))
        object.__setattr__(self, "filepath", validated_path)

        if self.destination is not None:
            clean_dest = self.destination.strip()
            if not clean_dest:
                raise config.CommandValidationError("Destination path cannot be empty.", field="destination", value=self.destination)

            if "\0" in clean_dest:
                raise config.CommandValidationError("Destination path cannot contain null bytes.", field="destination", value=self.destination)

            if any(ord(c) < 32 for c in clean_dest):
                raise config.CommandValidationError(
                    "Destination path cannot contain control characters or newlines.",
                    field="destination",
                    value=self.destination,
                )

            object.__setattr__(self, "destination", clean_dest)


class UploadFile(BaseFileCommand[UploadFileDTO]):
    """Upload and store a local file on the remote client without executing it.

    Encapsulates file transfer by reading the local file defined in
    ``UploadFileDTO``, encoding it, and instructing the client to store it
    locally using the ``STORE_FILE`` opcode.
    """

    def __init__(self, dto: UploadFileDTO, /) -> None:
        """Initialize UploadFile with validated parameters.

        Args:
            dto: Validated DTO containing the file path to upload.
        """

        super().__init__(dto, opcode=config.OperationCode.STORE_FILE)

    def _operation_arguments(self) -> tuple[str, ...]:
        """Return destination path if configured for file upload."""

        if self._dto.destination:
            return (self._dto.destination,)

        return ()
