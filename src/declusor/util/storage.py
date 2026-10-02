from pathlib import Path

from declusor import config


def load_file(filepath: str | Path, /) -> bytes:
    """Read a file from the filesystem.

    Args:
        filepath: The path to the file to read.

    Returns:
        The content of the file as bytes.

    Raises:
        InvalidOperation: If the file does not exist, is not a file, or cannot be read.
    """

    filepath = ensure_file_exists(filepath)

    try:
        with open(filepath, "rb") as f:
            return f.read()
    except OSError as e:
        raise config.StorageValidationError(f"could not read file {filepath!r}: {e}", path=filepath) from e


def try_load_file(filepath: str | Path, /) -> bytes | None:
    """Try to read a file from the filesystem.

    Args:
        filepath (str | Path): The path to the file to read.

    Returns:
        bytes | None: The content of the file as bytes, or None if the file could not be read.
    """

    try:
        return load_file(filepath)
    except (config.InvalidOperation, config.StorageError):
        return None


def ensure_file_exists(filepath: str | Path, /) -> Path:
    """Ensure file existence or raise an error.

    Args:
        filepath (str | Path): The path to the file.

    Returns:
        Path: The resolved file path.

    Raises:
        StorageValidationError: If the file does not exist, is not a file, is empty,
            or contains null bytes.
    """

    raw_path = str(filepath).strip()
    if not raw_path:
        raise config.StorageValidationError("File path cannot be empty.")

    if "\0" in raw_path:
        raise config.StorageValidationError("File path cannot contain null bytes.", path=filepath)

    filepath = Path(filepath).resolve()

    if not filepath.exists():
        raise config.StorageValidationError(f"file {filepath.name!r} does not exist", path=filepath)

    if not filepath.is_file():
        raise config.StorageValidationError(f"{filepath.name!r} is not a file", path=filepath)

    return filepath


def ensure_directory_exists(dirpath: str | Path, /) -> Path:
    """Ensure directory existence or raise an error.

    Args:
        dirpath (str | Path): The path to the directory.

    Returns:
        Path: The resolved directory path.

    Raises:
        StorageValidationError: If the directory does not exist, is not a directory, is empty,
            or contains null bytes.
    """

    raw_path = str(dirpath).strip()
    if not raw_path:
        raise config.StorageValidationError("Directory path cannot be empty.")

    if "\0" in raw_path:
        raise config.StorageValidationError("Directory path cannot contain null bytes.", path=dirpath)

    dirpath = Path(dirpath).resolve()

    if not dirpath.exists():
        raise config.StorageValidationError(f"directory {dirpath.name!r} does not exist", path=dirpath)

    if not dirpath.is_dir():
        raise config.StorageValidationError(f"{dirpath.name!r} is not a directory", path=dirpath)

    return dirpath
