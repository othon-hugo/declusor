"""Tests for ``declusor.util.security``.

Covers ``validate_file_extension`` (basic matching, case sensitivity, complex
filenames, input types) and ``validate_file_relative`` (directory containment,
path-traversal defence, input handling, edge cases).
"""

from pathlib import Path

import pytest

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_directory(tmp_path: Path) -> Path:
    """Create a temporary directory structure for path-validation tests."""


@pytest.fixture
def temp_file_in_directory(temp_directory: Path) -> Path:
    """Create a temporary file inside ``temp_directory``."""


# =============================================================================
# Tests: validate_file_extension — basic
# =============================================================================


def test_extension_allowed() -> None:
    """``"script.sh"`` with ``[".sh"]`` must return ``True``."""


def test_extension_disallowed() -> None:
    """``"script.py"`` with ``[".sh"]`` must return ``False``."""


def test_extension_empty_allowed_list() -> None:
    """An empty allowed list must always return ``False``."""


def test_extension_no_extension() -> None:
    """``"Makefile"`` must return ``False`` when only ``.sh`` is allowed."""


# =============================================================================
# Tests: validate_file_extension — case sensitivity
# =============================================================================


def test_extension_case_insensitive_file() -> None:
    """``"SCRIPT.SH"`` must match ``[".sh"]`` (case-insensitive)."""


def test_extension_case_insensitive_allowed() -> None:
    """``"script.sh"`` must match ``[".SH"]`` (case-insensitive)."""


def test_extension_mixed_case() -> None:
    """``"Script.Sh"`` must match ``[".sh"]``."""


# =============================================================================
# Tests: validate_file_extension — complex filenames
# =============================================================================


def test_extension_multiple_dots() -> None:
    """``"archive.tar.gz"`` must match against the *last* suffix (``".gz"``)."""


def test_extension_hidden_file_with_ext() -> None:
    """``".bashrc.sh"`` must match ``[".sh"]``."""


def test_extension_hidden_file_without_ext() -> None:
    """``".bashrc"`` must return ``False`` (empty suffix)."""


def test_extension_dot_only() -> None:
    """``"."`` edge case must be handled gracefully."""


# =============================================================================
# Tests: validate_file_extension — input types
# =============================================================================


def test_extension_path_object_input() -> None:
    """``Path("script.sh")`` must be accepted."""


def test_extension_string_input() -> None:
    """A plain ``str`` must be accepted."""


def test_extension_allowed_as_set() -> None:
    """A ``set`` of allowed extensions must work."""


def test_extension_allowed_as_tuple() -> None:
    """A ``tuple`` of allowed extensions must work."""


def test_extension_full_path() -> None:
    """``"/path/to/script.sh"`` must extract and match the extension."""


# =============================================================================
# Tests: validate_file_relative — basic
# =============================================================================


def test_relative_inside_base_dir(temp_directory: Path) -> None:
    """A file inside ``base_dir`` must return ``True``."""


def test_relative_outside_base_dir(temp_directory: Path) -> None:
    """A file outside ``base_dir`` must return ``False``."""


def test_relative_same_as_base_dir(temp_directory: Path) -> None:
    """A path equal to ``base_dir`` must return ``True``."""


# =============================================================================
# Tests: validate_file_relative — path-traversal defence
# =============================================================================


def test_relative_dotdot_traversal(temp_directory: Path) -> None:
    """``"../../../etc/passwd"`` must resolve outside and return ``False``."""


def test_relative_absolute_path_mismatch() -> None:
    """Completely disjoint paths must return ``False``."""


def test_relative_symlink_attack(temp_directory: Path) -> None:
    """A symlink pointing outside ``base_dir`` must return ``False`` after resolution."""


# =============================================================================
# Tests: validate_file_relative — input handling
# =============================================================================


def test_relative_string_inputs() -> None:
    """Both arguments as ``str`` must be accepted."""


def test_relative_mixed_inputs(temp_directory: Path) -> None:
    """One ``str`` and one ``Path`` must be accepted."""


def test_relative_resolves_relative_paths(temp_directory: Path) -> None:
    """Relative paths must be resolved to absolute before comparison."""


# =============================================================================
# Tests: validate_file_relative — edge cases
# =============================================================================


def test_relative_unicode_paths(temp_directory: Path) -> None:
    """Unicode characters in paths must be handled correctly."""


def test_relative_paths_with_spaces(temp_directory: Path) -> None:
    """Spaces in paths must be handled correctly."""


def test_relative_nonexistent_paths() -> None:
    """Non-existent paths must still compute the relationship correctly."""


def test_relative_root_as_base() -> None:
    """``base_dir="/"`` must make all absolute paths relative."""


def test_relative_nested_subdirectory(temp_directory: Path) -> None:
    """A deeply nested path must still return ``True``."""


def test_relative_similar_prefix_names(temp_directory: Path) -> None:
    """``/home/user2/file`` must *not* match ``base_dir=/home/user``."""
