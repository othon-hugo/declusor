from pathlib import Path

from declusor.util import security


def test_validate_file_extension_matching() -> None:
    """Verify allowed extensions return True case-insensitively."""

    assert security.validate_file_extension("test.py", [".py", ".sh"]) is True
    assert security.validate_file_extension("test.PY", [".py"]) is True
    assert security.validate_file_extension(Path("/tmp/script.sh"), [".sh"]) is True


def test_validate_file_extension_non_matching() -> None:
    """Verify non-allowed extensions return False."""

    assert security.validate_file_extension("test.txt", [".py", ".sh"]) is False
    assert security.validate_file_extension("test", [".py"]) is False


def test_validate_file_relative_inside(tmp_path: Path) -> None:
    """Verify paths inside base directory return True."""

    child = tmp_path / "sub" / "file.txt"
    assert security.validate_file_relative(child, tmp_path) is True


def test_validate_file_relative_outside(tmp_path: Path) -> None:
    """Verify path traversal escapes return False."""

    base = tmp_path / "sandbox"
    base.mkdir()
    outside = tmp_path / "other" / "file.txt"
    traversal = base / ".." / "other" / "file.txt"

    assert security.validate_file_relative(outside, base) is False
    assert security.validate_file_relative(traversal, base) is False


def test_generate_nonce_default_length() -> None:
    """Verify default nonce generates 32 hex chars (16 bytes) with high entropy."""

    nonce1 = security.generate_nonce()
    nonce2 = security.generate_nonce()

    assert len(nonce1) == 32
    assert len(nonce2) == 32
    assert nonce1 != nonce2
    int(nonce1, 16)


def test_generate_nonce_custom_length() -> None:
    """Verify generate_nonce honors custom byte lengths."""

    nonce = security.generate_nonce(nbytes=8)

    assert len(nonce) == 16
    int(nonce, 16)
