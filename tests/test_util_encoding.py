"""Tests for the ``declusor.util.encoding`` module."""

import pytest

from declusor.util import encoding


# =============================================================================
# Tests: encoding.quote (Shell string escaping)
# =============================================================================

def test_quote_escapes_special_shell_characters() -> None:
    """Quoting a string with special shell characters must return a safely escaped token."""

    # ARRANGE: Define a string with potential injection characters like spaces and semi-colons
    malicious_input = "echo 'hello'; rm -rf /"

    # ACT: Run the ``encoding.quote`` escaping function
    escaped_output = encoding.quote(malicious_input)

    # ASSERT: The entire string should be wrapped as a single shell-safe unit
    assert escaped_output == "'echo '\"'\"'hello'\"'\"'; rm -rf /'"


# =============================================================================
# Tests: encoding.format_template (Template string formatting)
# =============================================================================

def test_format_template_substitutes_matched_placeholders() -> None:
    """Formatting a template must substitute provided keyword arguments into matching placeholders."""

    # ARRANGE: Create a template string and substitution variables
    template = "Hello $name, your score is ${score}."

    # ACT: Call ``encoding.format_template`` with corresponding keywords
    result = encoding.format_template(template, name="Alice", score=100)

    # ASSERT: Expected fields should be parsed and overwritten properly
    assert result == "Hello Alice, your score is 100."

def test_format_template_ignores_unmatched_placeholders() -> None:
    """Formatting a template with missing arguments must leave the unmatched placeholders unchanged."""

    # ARRANGE: Create a template with multiple variables
    template = "Expected $filled and $missing variables."

    # ACT: Evaluate the template with incomplete argument mapping
    result = encoding.format_template(template, filled="handled")

    # ASSERT: The missing item should remain as the raw placeholder designator
    assert result == "Expected handled and $missing variables."


# =============================================================================
# Tests: encoding.convert_to_bytes (String to bytes conversion)
# =============================================================================

def test_convert_to_bytes_encodes_string_as_utf8() -> None:
    """Converting a string to bytes must return its UTF-8 encoded bytes representation."""

    # ARRANGE: Provide a standard string
    data_str = "ascii_data"

    # ACT: Translate it via ``encoding.convert_to_bytes``
    result = encoding.convert_to_bytes(data_str)

    # ASSERT: Should yield matching exact bytes value
    assert result == b"ascii_data"

def test_convert_to_bytes_returns_bytes_unchanged() -> None:
    """Converting a bytes object to bytes must return the original object unchanged."""

    # ARRANGE: Construct an explicit binary snippet
    data_bytes = b"already_bytes"

    # ACT: Try converting the already-binary data
    result = encoding.convert_to_bytes(data_bytes)

    # ASSERT: Identity should remain identical without side effects
    assert result is data_bytes


# =============================================================================
# Tests: encoding.convert_bytes_to_hex (Bytes to hex conversion)
# =============================================================================

def test_convert_bytes_to_hex_returns_hex_string() -> None:
    """Converting bytes to hex must return the correct hexadecimal string representation."""

    # ARRANGE: Input distinct bytes representation
    data = b"\xde\xad\xbe\xef"

    # ACT: Convert via ``encoding.convert_bytes_to_hex``
    result = encoding.convert_bytes_to_hex(data)

    # ASSERT: Ensure standardized representation using backslash-x formatted string values
    assert result == r"\xde\xad\xbe\xef"


# =============================================================================
# Tests: encoding.convert_to_base64 (Data to Base64 conversion)
# =============================================================================

def test_convert_to_base64_encodes_string_to_b64() -> None:
    """Converting a string to Base64 must return the correct Base64 encoded string."""

    # ARRANGE: Basic plaintext snippet
    data = "hello world"

    # ACT: Base64 encoding via ``encoding.convert_to_base64``
    result = encoding.convert_to_base64(data)

    # ASSERT: Valid B64 signature evaluated
    assert result == "aGVsbG8gd29ybGQ="


# =============================================================================
# Tests: encoding.convert_base64_to_bytes (Base64 to bytes conversion)
# =============================================================================

def test_convert_base64_to_bytes_decodes_b64_to_bytes() -> None:
    """Converting a Base64 string to bytes must decode and return the original bytes."""

    # ARRANGE: Valid B64 payload
    b64_data = "aGVsbG8gd29ybGQ="

    # ACT: Reverse evaluation via ``encoding.convert_base64_to_bytes``
    result = encoding.convert_base64_to_bytes(b64_data)

    # ASSERT: Decrypted strictly to the internal sequence
    assert result == b"hello world"


# =============================================================================
# Tests: encoding hash functions (MD5, SHA256, SHA384, SHA512)
# =============================================================================

def test_hash_md5_returns_correct_digest() -> None:
    """Hashing data with MD5 must return the correct message digest bytes."""

    # ARRANGE: Plaintext test seed
    data = "test"

    # ACT: Generate MD5 signature
    result = encoding.hash_md5(data)

    # ASSERT: Binary hash value correlates properly to MD5 derivation rules
    assert result.hex() == "098f6bcd4621d373cade4e832627b4f6"

def test_hash_sha256_returns_correct_digest() -> None:
    """Hashing data with SHA256 must return the correct sequence of digest bytes."""

    # ARRANGE: Plaintext test seed
    data = "test"

    # ACT: Generate SHA256 signature
    result = encoding.hash_sha256(data)

    # ASSERT: Compare binary checksum against known standard definition
    assert result.hex() == "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"

def test_hash_sha384_returns_correct_digest() -> None:
    """Hashing data with SHA384 must return the correct sequence of digest bytes."""

    # ARRANGE: Plaintext test seed
    data = "test"

    # ACT: Run calculation via ``encoding.hash_sha384``
    result = encoding.hash_sha384(data)

    # ASSERT: Conformity check on output hexadecimal derivation
    assert result.hex() == "768412320f7b0aa5812fce428dc4706b3cae50e02a64caa16a782249bfe8efc4b7ef1ccb126255d196047dfedf17a0a9"

def test_hash_sha512_returns_correct_digest() -> None:
    """Hashing data with SHA512 must return the correct sequence of digest bytes."""

    # ARRANGE: Plaintext test seed
    data = "test"

    # ACT: Convert and retrieve SHA512 sequence
    result = encoding.hash_sha512(data)

    # ASSERT: The produced deterministic digest is robust
    assert result.hex() == "ee26b0dd4af7e749aa1a8ee3c10ae9923f618980772e473f8819a5d4940e0db27ac185f8a0e1d5f84f88bc887fd67b143732c304cc5fa9ad8e6f57f50028a8ff"
