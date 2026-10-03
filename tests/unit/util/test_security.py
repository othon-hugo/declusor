"""Unit tests for the security utility functions."""

import re
from collections.abc import Generator
from pathlib import Path

import pytest

from declusor.util import security


class TestValidateFileExtension:
    """Tests for validate_file_extension."""

    def test_validate_file_extension__matching_extension_str__returns_true(self) -> None:
        """Verify str path with matching extension returns True."""

        assert security.validate_file_extension("script.py", [".py", ".sh"]) is True

    def test_validate_file_extension__matching_extension_path__returns_true(self) -> None:
        """Verify Path object with matching extension returns True."""

        assert security.validate_file_extension(Path("/tmp/script.sh"), [".sh"]) is True

    def test_validate_file_extension__uppercase_file_extension__returns_true(self) -> None:
        """Verify case-insensitivity when file has uppercase extension."""

        assert security.validate_file_extension("DOCUMENT.PDF", [".pdf"]) is True

    def test_validate_file_extension__uppercase_allowed_extension__returns_true(self) -> None:
        """Verify case-insensitivity when allowed list has uppercase extension."""

        assert security.validate_file_extension("script.py", [".PY"]) is True

    def test_validate_file_extension__unallowed_extension__returns_false(self) -> None:
        """Verify unallowed extension returns False."""

        assert security.validate_file_extension("script.rb", [".py", ".sh"]) is False

    def test_validate_file_extension__no_extension_when_empty_extension_not_allowed__returns_false(self) -> None:
        """Verify file without extension returns False when empty string not in allowed list."""

        assert security.validate_file_extension("Makefile", [".py", ".sh"]) is False

    def test_validate_file_extension__no_extension_when_empty_extension_allowed__returns_true(self) -> None:
        """Verify file without extension returns True when empty string is allowed."""

        assert security.validate_file_extension("Makefile", ["", ".sh"]) is True

    def test_validate_file_extension__empty_allowed_extensions__returns_false(self) -> None:
        """Verify empty allowed extensions collection always returns False."""

        assert security.validate_file_extension("script.py", []) is False

    def test_validate_file_extension__multi_dot_filename_matches_last_suffix__returns_true(self) -> None:
        """Verify multi-dot filename suffix matches against the final extension."""

        assert security.validate_file_extension("archive.tar.gz", [".gz"]) is True

    def test_validate_file_extension__multi_dot_filename_compound_suffix_not_matched__returns_false(self) -> None:
        """Verify compound suffix without dot splitting does not match single suffix."""

        assert security.validate_file_extension("archive.tar.gz", [".tar.gz"]) is False

    def test_validate_file_extension__allowed_extension_without_leading_dot__returns_false(self) -> None:
        """Verify allowed extension lacking leading dot does not match dotted suffix."""

        assert security.validate_file_extension("script.py", ["py"]) is False

    def test_validate_file_extension__generator_allowed_extensions__returns_true(self) -> None:
        """Verify non-collection generator iterable is accepted for allowed extensions."""

        def ext_gen() -> Generator[str, None, None]:
            yield ".py"
            yield ".sh"

        assert security.validate_file_extension("script.py", ext_gen()) is True


class TestValidateFileRelative:
    """Tests for validate_file_relative."""

    def test_validate_file_relative__direct_child__returns_true(self, tmp_path: Path) -> None:
        """Verify direct child file inside base directory returns True."""

        child = tmp_path / "child.txt"
        child.touch()

        assert security.validate_file_relative(child, tmp_path) is True

    def test_validate_file_relative__nested_child__returns_true(self, tmp_path: Path) -> None:
        """Verify deeply nested file inside base directory returns True."""

        nested = tmp_path / "sub" / "deep" / "file.txt"
        nested.parent.mkdir(parents=True)
        nested.touch()

        assert security.validate_file_relative(nested, tmp_path) is True

    def test_validate_file_relative__base_dir_itself__returns_true(self, tmp_path: Path) -> None:
        """Verify base directory path evaluated against itself returns True."""

        assert security.validate_file_relative(tmp_path, tmp_path) is True

    def test_validate_file_relative__string_arguments__returns_true(self, tmp_path: Path) -> None:
        """Verify string paths are accepted and validated correctly."""

        child = tmp_path / "child.txt"
        child.touch()

        assert security.validate_file_relative(str(child), str(tmp_path)) is True

    def test_validate_file_relative__outside_sibling_path__returns_false(self, tmp_path: Path) -> None:
        """Verify unrelated path outside base directory returns False."""

        base = tmp_path / "sandbox"
        base.mkdir()
        outside = tmp_path / "other" / "file.txt"

        assert security.validate_file_relative(outside, base) is False

    def test_validate_file_relative__parent_traversal_escape__returns_false(self, tmp_path: Path) -> None:
        """Verify dot-dot traversal escaping base directory returns False."""

        base = tmp_path / "sandbox"
        base.mkdir()
        traversal = base / ".." / "other.txt"

        assert security.validate_file_relative(traversal, base) is False

    def test_validate_file_relative__internal_traversal_remaining_inside__returns_true(self, tmp_path: Path) -> None:
        """Verify traversal containing dot-dot that remains within base directory returns True."""

        base = tmp_path / "sandbox"
        sub = base / "sub"
        sub.mkdir(parents=True)
        internal = sub / ".." / "sub" / "file.txt"

        assert security.validate_file_relative(internal, base) is True

    def test_validate_file_relative__symlink_escaping_base_dir__returns_false(self, tmp_path: Path) -> None:
        """Verify symlink inside base directory pointing outside resolves and returns False."""

        base = tmp_path / "sandbox"
        base.mkdir()
        outside = tmp_path / "outside.txt"
        outside.touch()

        link_inside = base / "escape_link"
        link_inside.symlink_to(outside)

        assert security.validate_file_relative(link_inside, base) is False

    def test_validate_file_relative__symlink_entering_base_dir__returns_true(self, tmp_path: Path) -> None:
        """Verify symlink outside base directory pointing inside resolves and returns True."""

        base = tmp_path / "sandbox"
        base.mkdir()
        inside = base / "target.txt"
        inside.touch()

        outside_link = tmp_path / "outside_link"
        outside_link.symlink_to(inside)

        assert security.validate_file_relative(outside_link, base) is True


class TestGenerateNonce:
    """Tests for generate_nonce."""

    def test_generate_nonce__default_nbytes__returns_32_character_hex_string(self) -> None:
        """Verify default call produces a 32-character hexadecimal string."""

        token = security.generate_nonce()

        assert len(token) == 32

    def test_generate_nonce__custom_nbytes__returns_proportional_hex_string(self) -> None:
        """Verify custom nbytes produces a string of length 2 * nbytes."""

        token = security.generate_nonce(nbytes=8)

        assert len(token) == 16

    def test_generate_nonce__zero_nbytes__returns_empty_string(self) -> None:
        """Verify zero nbytes produces an empty string."""

        token = security.generate_nonce(nbytes=0)

        assert token == ""

    def test_generate_nonce__negative_nbytes__raises_value_error(self) -> None:
        """Verify negative nbytes raises ValueError."""

        with pytest.raises(ValueError, match="negative argument not allowed"):
            security.generate_nonce(nbytes=-1)

    def test_generate_nonce__character_set__contains_only_lowercase_hex_digits(self) -> None:
        """Verify generated token strictly matches hexadecimal lowercase characters."""

        token = security.generate_nonce(nbytes=32)

        assert re.fullmatch(r"[0-9a-f]{64}", token) is not None

    def test_generate_nonce__repeated_calls__produces_distinct_values(self) -> None:
        """Verify successive invocations generate unique nonces."""

        token_a = security.generate_nonce()
        token_b = security.generate_nonce()

        assert token_a != token_b
