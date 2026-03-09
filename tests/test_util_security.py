"""Tests for the ``declusor.util.security`` module."""

from pathlib import Path

from declusor.util import security


# =============================================================================
# Tests: security.validate_file_extension (Extension checking)
# =============================================================================

def test_validate_file_extension_succeeds_for_allowed_extensions() -> None:
    """Validating a file with an allowed extension must return True."""

    # ARRANGE: Define list of allowed filetypes and a valid document path
    allowed = [".txt", ".md"]
    test_file = Path("readme.md")

    # ACT: Run evaluation for checking path extensions
    result = security.validate_file_extension(test_file, allowed)

    # ASSERT: Should match and validate the operation
    assert result is True

def test_validate_file_extension_ignores_case() -> None:
    """Validating an extension with different casing from the allowed list must return True."""

    # ARRANGE: Provide lowercase requirements alongside uppercase input extension
    allowed = [".CSV", ".JSON"]
    test_file = Path("data.json")

    # ACT: Validate file extension
    result = security.validate_file_extension(test_file, allowed)

    # ASSERT: The evaluation internally forces case-insensitive matching
    assert result is True

def test_validate_file_extension_fails_for_disallowed_extensions() -> None:
    """Validating a file with an unlisted extension must return False."""

    # ARRANGE: Define authorized constraints and a violating input extension
    allowed = [".txt"]
    test_file = "image.png"

    # ACT: Execute path resolution
    result = security.validate_file_extension(test_file, allowed)

    # ASSERT: Result properly identifies the failed constraint
    assert result is False

def test_validate_file_extension_fails_for_missing_extension() -> None:
    """Validating a file with no extension must return False if not explicitly authorized."""

    # ARRANGE: Provide a generic file path without a dot extension
    allowed = [".txt"]
    test_file = "Dockerfile"

    # ACT: Determine extension validity
    result = security.validate_file_extension(test_file, allowed)

    # ASSERT: Missing extensions properly default to a negative check
    assert result is False


# =============================================================================
# Tests: security.validate_file_relative (Path directory constraints)
# =============================================================================

def test_validate_file_relative_succeeds_for_child_paths() -> None:
    """Validating a path correctly nested within the base directory must return True."""

    # ARRANGE: Base environment path and standard inner descendant path targeting it
    base_dir = Path("/etc/declusor")
    child_path = Path("/etc/declusor/config/settings.yml")

    # ACT: Confirm path validation resolves correctly
    result = security.validate_file_relative(child_path, base_dir)

    # ASSERT: Nested structures identify correctly
    assert result is True

def test_validate_file_relative_fails_for_external_paths() -> None:
    """Validating a path pointing outside the base directory structure must return False."""

    # ARRANGE: Standard environment isolation and externally resolving target (using ../)
    base_dir = "/home/user/app/data"
    malicious_path = "/home/user/app/data/../../.ssh/id_rsa"

    # ACT: Try to detect path traversal bounds break
    result = security.validate_file_relative(malicious_path, base_dir)

    # ASSERT: Deny path transversal behavior attempting to access restricted parent resources
    assert result is False
