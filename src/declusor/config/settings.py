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

    def for_client(self, client_name: str, /) -> "ClientDataPaths":
        """Derive namespaced data paths for a specific client plugin.

        Resolves paths under ``data/<client_name>/`` in the namespaced
        hierarchy introduced to support multiple client plugin runtimes.

        Args:
            client_name: The registered name of the client plugin (e.g. ``py_socket``).

        Returns:
            Immutable client-scoped paths derived from the root data directory.
        """
        client_root = self.root / client_name
        return ClientDataPaths(
            root=client_root,
            launcher=client_root / "launchers",
            helpers=client_root / "helpers",
            modules=client_root / "modules",
        )


@dataclass(frozen=True)
class ClientDataPaths:
    """Namespaced filesystem paths for a specific client plugin.

    Provides access to the launcher script, helper libraries, and module
    payloads scoped to a single client under the namespaced data hierarchy
    (e.g. ``data/py_socket/launchers/``, ``data/py_socket/helpers/``).
    """

    root: Path
    """Root directory of the client data namespace (e.g. ``data/py_socket/``)."""

    launcher: Path
    """Directory containing the client launcher scripts."""

    helpers: Path
    """Directory containing helper library scripts loaded at session init."""

    modules: Path
    """Directory containing on-demand payload modules."""


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
