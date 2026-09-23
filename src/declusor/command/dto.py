from dataclasses import dataclass
from pathlib import Path

from declusor import config, util


@dataclass(frozen=True)
class ExecuteCommandDTO:
    """Data transfer object containing parameters for remote command execution.

    Encapsulates and validates the raw command line string to be transmitted
    and executed on the remote client.

    Attributes:
        command_line: Non-empty shell command line string.

    Raises:
        InvalidOperation: If ``command_line`` is empty or consists solely of whitespace.
    """

    command_line: str

    def __post_init__(self) -> None:
        if not self.command_line or not self.command_line.strip():
            raise config.InvalidOperation("Command line cannot be empty.")


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


@dataclass(frozen=True)
class LoadModuleDTO:
    """Data transfer object containing parameters for loading a client module.

    Encapsulates and validates the name of the module to load from the client's
    module repository. Prevents path traversal vulnerabilities.

    Attributes:
        module_name: Clean module identifier (e.g. ``discovery/sysinfo``).

    Raises:
        InvalidOperation: If ``module_name`` is empty or attempts directory traversal.
    """

    module_name: str

    def __post_init__(self) -> None:
        if not self.module_name or not self.module_name.strip():
            raise config.InvalidOperation("Module name cannot be empty.")

        clean_name = self.module_name.strip()

        if ".." in clean_name or clean_name.startswith("/") or "\\" in clean_name:
            raise config.InvalidOperation(f"Invalid module name '{self.module_name}': path traversal is not permitted.")


@dataclass(frozen=True)
class ShellDTO:
    """Data transfer object configuring an interactive shell session.

    Attributes:
        banner: Optional informational banner message displayed upon entering shell mode.
    """

    banner: str | None = None
