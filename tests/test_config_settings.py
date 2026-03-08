"""Tests for ``declusor.config.settings`` (``Settings``, ``BasePath``).

Verifies that configuration constants are well-typed and that ``BasePath``
directory entries resolve correctly under the project root.
"""

from pathlib import Path

import pytest

# =============================================================================
# Tests: Settings — project metadata
# =============================================================================


def test_settings_project_name_is_nonempty_string() -> None:
    """``Settings.PROJECT_NAME`` must be a non-empty ``str``."""


def test_settings_project_description_is_nonempty_string() -> None:
    """``Settings.PROJECT_DESCRIPTION`` must be a non-empty ``str``."""


# =============================================================================
# Tests: BasePath — root directory
# =============================================================================


def test_basepath_root_dir_is_path() -> None:
    """``BasePath.ROOT_DIR`` must be a ``pathlib.Path`` object."""


def test_basepath_root_dir_is_absolute() -> None:
    """``BasePath.ROOT_DIR.is_absolute()`` must be ``True``."""


def test_basepath_root_dir_exists() -> None:
    """``BasePath.ROOT_DIR`` must point to an existing directory."""


# =============================================================================
# Tests: BasePath — data directory
# =============================================================================


def test_basepath_data_dir_is_path() -> None:
    """``BasePath.DATA_DIR`` must be a ``pathlib.Path`` object."""


def test_basepath_data_dir_is_child_of_root() -> None:
    """``BasePath.DATA_DIR`` must be a subdirectory of ``ROOT_DIR``."""


def test_basepath_data_dir_named_data() -> None:
    """``BasePath.DATA_DIR.name`` must equal ``"data"``."""


# =============================================================================
# Tests: BasePath — subdirectories
# =============================================================================


def test_basepath_clients_dir_is_child_of_data() -> None:
    """``BasePath.CLIENTS_DIR`` must reside under ``DATA_DIR``."""


def test_basepath_modules_dir_is_child_of_data() -> None:
    """``BasePath.MODULES_DIR`` must reside under ``DATA_DIR``."""


def test_basepath_library_dir_is_child_of_data() -> None:
    """``BasePath.LIBRARY_DIR`` must reside under ``DATA_DIR``."""


def test_basepath_clients_dir_named_clients() -> None:
    """``BasePath.CLIENTS_DIR.name`` must equal ``"clients"``."""


def test_basepath_modules_dir_named_modules() -> None:
    """``BasePath.MODULES_DIR.name`` must equal ``"modules"``."""


def test_basepath_library_dir_named_library() -> None:
    """``BasePath.LIBRARY_DIR.name`` must equal ``"library"``."""
