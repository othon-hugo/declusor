from pathlib import Path

from declusor import config
from declusor.util import security


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
        raise config.InvalidOperation(f"could not read file {filepath!r}: {e}") from e


def try_load_file(filepath: str | Path, /) -> bytes | None:
    """Try to read a file from the filesystem.

    Args:
        filepath (str | Path): The path to the file to read.

    Returns:
        bytes | None: The content of the file as bytes, or None if the file could not be read.
    """

    try:
        return load_file(filepath)
    except config.InvalidOperation:
        return None


def ensure_file_exists(filepath: str | Path, /) -> Path:
    """Ensure file existence or raise an error.

    Args:
        filepath (str | Path): The path to the file.

    Returns:
        Path: The resolved file path.

    Raises:
        InvalidOperation: If the file does not exist or is not a file.
    """

    filepath = Path(filepath).resolve()

    if not filepath.exists():
        raise config.InvalidOperation(f"file {filepath.name!r} does not exist")

    if not filepath.is_file():
        raise config.InvalidOperation(f"{filepath.name!r} is not a file")

    return filepath


def ensure_directory_exists(dirpath: str | Path, /) -> Path:
    """Ensure directory existence or raise an error.

    Args:
        dirpath (str | Path): The path to the directory.

    Returns:
        Path: The resolved directory path.

    Raises:
        InvalidOperation: If the directory does not exist or is not a directory.
    """

    dirpath = Path(dirpath).resolve()

    if not dirpath.exists():
        raise config.InvalidOperation(f"directory {dirpath.name!r} does not exist")

    if not dirpath.is_dir():
        raise config.InvalidOperation(f"{dirpath.name!r} is not a directory")

    return dirpath
