from pathlib import Path
from typing import Final

from .enums import ExecutionMode


class Settings:
    """Configuration settings for Declusor."""

    PROJECT_NAME: Final[str] = "declusor"
    """Name of the project."""

    PROJECT_DESCRIPTION: Final[str] = "a versatile tool for delivering Bash payloads to Linux systems."
    """Short description of the project."""

    DEFAULT_EXECUTION_MODE: Final[ExecutionMode] = ExecutionMode.CLI
    """Default application execution mode."""

    DEFAULT_SERVER_ACK: Final[bytes] = b"\x00"
    """Default server acknowledgment byte sequence."""

    DEFAULT_CLIENT_ACK_SEED: Final[bytes] = b"declusor"
    """Default client acknowledgment seed used for SHA-256 calculation."""


class BasePath:
    """Base paths for Declusor project directories."""

    ROOT_DIR = Path(__file__).resolve().parents[3]
    """Normalized root directory of the project."""

    PLUGINS_DIR = (ROOT_DIR / "plugins").resolve()
    """Root plugins directory for built-in and repository-level plugins."""

    USER_DIR = (Path.home() / ".declusor").resolve()
    """Default user-level configuration and runtime directory."""

    USER_PLUGINS_DIR = (USER_DIR / "plugins").resolve()
    """Default user-level plugins directory for drop-in extensions."""
