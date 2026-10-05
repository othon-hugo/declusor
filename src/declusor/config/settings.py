from pathlib import Path
from typing import Final

from .enums import DeclusorPlugins, ExecutionMode, LauncherOutputMode

PROJECT_NAME: Final[str] = "declusor"
"""Name of the project."""

PROJECT_DESCRIPTION: Final[str] = "A fast, modular, and extensible reverse-shell framework and payload delivery handler."
"""Short description of the project."""

ROOT_DIR: Final[Path] = Path(__file__).resolve().parents[3]
"""Normalized root directory of the project."""

PLUGINS_DIR: Final[Path] = (ROOT_DIR / "plugins").resolve()
"""Root plugins directory for built-in and repository-level plugins."""

USER_DIR: Final[Path] = (Path.home() / ".declusor").resolve()
"""Default user-level configuration and runtime directory."""

USER_PLUGINS_DIR: Final[Path] = (USER_DIR / "plugins").resolve()
"""Default user-level plugins directory for drop-in extensions."""

DEFAULT_SERVER_ACK: Final[bytes] = b"\x00"
"""Default server acknowledgment byte sequence."""

DEFAULT_CLIENT_ACK_SEED: Final[bytes] = b"declusor"
"""Default client acknowledgment seed used for SHA-256 calculation."""

DEFAULT_CONNECTION_TIMEOUT: Final[float | None] = 1.0
"""Default connection timeout in seconds for network operations; None disables it."""

DEFAULT_DECLUSOR_PLUGIN = DeclusorPlugins.SHELL_SOCKET
"""Default client plugin identifier."""

DEFAULT_EXECUTION_MODE = ExecutionMode.CLI
"""Default application execution mode."""

DEFAULT_LAUNCHER_OUTPUT_MODE: Final[LauncherOutputMode] = LauncherOutputMode.TERMINAL
"""Default client launcher output delivery mode."""

DEFAULT_XOR_KEY: Final[bytes] = b"declusor"
"""Default obfuscation key for XOR transport layer."""

MAX_TLV_FRAME_SIZE: Final[int] = 64 * 1024 * 1024
"""Maximum payload size in bytes for a Python plugin TLV frame."""

DEFAULT_COMPLETION_BLOCKED_NAMES: Final[frozenset[str]] = frozenset(
    {
        "__pycache__",
        ".git",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".venv",
        "venv",
        ".env",
        ".idea",
        ".vscode",
        ".tox",
        ".coverage",
        ".DS_Store",
    }
)
"""Common file and directory names ignored during interactive autocomplete."""

DEFAULT_COMPLETION_BLOCKED_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {
        ".pyc",
        ".pyo",
        ".pyd",
        ".swp",
        ".swo",
        ".bak",
        "~",
    }
)
"""Common file extensions ignored during interactive autocomplete."""
