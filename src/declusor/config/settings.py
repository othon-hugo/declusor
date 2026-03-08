from pathlib import Path


class Settings:
    """Configuration settings for Declusor."""

    PROJECT_NAME = "declusor"
    """Name of the project."""

    PROJECT_DESCRIPTION = "a versatile tool for delivering Bash payloads to Linux systems."
    """Short description of the project."""


class BasePath:
    """Base paths for Declusor project directories."""

    ROOT_DIR = Path(__file__).resolve().parents[3]
    """Normalized root directory of the project."""

    DATA_DIR = (ROOT_DIR / "data").resolve()
    """Normalized data directory path."""

    CLIENTS_DIR = (DATA_DIR / "clients").resolve()
    """Normalized clients directory path."""

    MODULES_DIR = (DATA_DIR / "modules").resolve()
    """Normalized modules directory path."""

    LIBRARY_DIR = (DATA_DIR / "library").resolve()
    """Normalized library directory path."""
