"""Tests for ``declusor.util.encoding``.

Covers ``convert_bytes_to_hex``, ``convert_to_base64``,
``convert_base64_to_bytes``, and round-trip integrity.
"""

import pytest

# =============================================================================
# Tests: convert_bytes_to_hex
# =============================================================================


def test_bytes_to_hex_basic() -> None:
    """``b'\\x00\\xff'`` must produce the string ``'\\x00\\xff'``."""


def test_bytes_to_hex_empty_input() -> None:
    """``b''`` must produce an empty string."""


def test_bytes_to_hex_printable_ascii() -> None:
    """Printable ASCII bytes must still be hex-encoded (e.g. ``b'A'`` → ``'\\x41'``)."""


def test_bytes_to_hex_preserves_order() -> None:
    """Byte order must be preserved in the output."""


def test_bytes_to_hex_all_possible_values() -> None:
    """Every byte value ``0x00``–``0xFF`` must be correctly formatted."""


# =============================================================================
# Tests: convert_to_base64
# =============================================================================


def test_to_base64_from_string() -> None:
    """``"hello"`` must produce the base64 string ``"aGVsbG8="``."""


def test_to_base64_from_bytes() -> None:
    """``b"hello"`` must produce the same result as the string input."""


def test_to_base64_empty_string() -> None:
    """An empty string must produce an empty base64 output."""


def test_to_base64_empty_bytes() -> None:
    """Empty bytes must produce an empty base64 output."""


def test_to_base64_binary_data() -> None:
    """Non-UTF-8 binary bytes must produce a valid base64 string."""


def test_to_base64_unicode_string() -> None:
    """Unicode characters must be UTF-8 encoded before base64 encoding."""


def test_to_base64_padding() -> None:
    """Strings of length 1, 2, 3 must be properly padded with ``=`` / ``==``."""


# =============================================================================
# Tests: convert_base64_to_bytes
# =============================================================================


def test_base64_to_bytes_basic() -> None:
    """``"aGVsbG8="`` must decode to ``b"hello"``."""


def test_base64_to_bytes_empty() -> None:
    """An empty string must decode to ``b""``."""


def test_base64_to_bytes_binary_data() -> None:
    """A base64 string encoding binary data must decode to the original bytes."""


def test_base64_to_bytes_roundtrip() -> None:
    """``convert_base64_to_bytes(convert_to_base64(data))`` must equal the original."""


def test_base64_to_bytes_no_padding() -> None:
    """Base64 without padding (``"aGVsbG8"``) must either decode or raise consistently."""


def test_base64_to_bytes_invalid_characters() -> None:
    """Invalid characters (``"!!invalid!!"`` ) must raise ``binascii.Error``."""


# =============================================================================
# Tests: Round-trip / Integration
# =============================================================================


def test_roundtrip_preserves_all_byte_values() -> None:
    """Encoding then decoding all 256 byte values must be lossless."""


def test_hex_is_shell_compatible() -> None:
    """The hex output must be usable in a shell ``echo -e`` command."""
