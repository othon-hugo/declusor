from dataclasses import dataclass
from pathlib import Path
from typing import Final


class Settings:
    """Configuration settings for Declusor."""

    PROJECT_NAME: Final[str] = "declusor"
    """Name of the project."""

    PROJECT_DESCRIPTION: Final[str] = "a versatile tool for delivering Bash payloads to Linux systems."
    """Short description of the project."""

    DEFAULT_SERVER_ACK: Final[bytes] = b"\x00"
    """Default server acknowledgment byte sequence."""

    DEFAULT_CLIENT_ACK_SEED: Final[bytes] = b"\xba\xdc\x00\xff\xee"
    """Default client acknowledgment seed used for SHA-256 calculation."""


@dataclass(frozen=True)
class DataPaths:
    """Filesystem paths used by a Declusor client runtime."""

    root: Path
    """Root directory containing the Declusor data directories."""

    clients: Path
    """Directory containing client bootstrap templates."""

    modules: Path
    """Directory containing payload modules."""

    library: Path
    """Directory containing reusable client libraries."""

    @classmethod
    def from_root(cls, root: Path, /) -> "DataPaths":
        """Build normalized data paths from a root directory.

        Args:
            root: Directory containing ``clients``, ``modules`` and ``library``.

        Returns:
            Immutable paths derived from ``root``.
        """

        normalized_root = root.expanduser().resolve()
        return cls(
            root=normalized_root,
            clients=normalized_root / "clients",
            modules=normalized_root / "modules",
            library=normalized_root / "library",
        )


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

    DATA_PATHS = DataPaths.from_root(DATA_DIR)
    """Default data paths used during development."""
