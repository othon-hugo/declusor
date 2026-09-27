import hashlib

from declusor.util import encoding


def test_quote_escapes_shell_tokens() -> None:
    """Verify quote wraps arguments with special characters safely."""

    assert encoding.quote("hello") == "hello"
    assert encoding.quote("hello world") == "'hello world'"
    assert encoding.quote("a; rm -rf /") == "'a; rm -rf /'"


def test_format_template_substitutions() -> None:
    """Verify safe_substitute replaces matching keys and preserves others."""

    template = "HOST=$HOST PORT=$PORT EXTRA=$EXTRA"
    result = encoding.format_template(template, HOST="127.0.0.1", PORT="8080")
    assert result == "HOST=127.0.0.1 PORT=8080 EXTRA=$EXTRA"


def test_convert_to_bytes() -> None:
    """Verify conversion of str and bytes to bytes."""

    assert encoding.convert_to_bytes("hello") == b"hello"
    assert encoding.convert_to_bytes(b"world") == b"world"


def test_convert_bytes_to_hex() -> None:
    """Verify hex string conversion formatted with \\x escape prefixes."""

    assert encoding.convert_bytes_to_hex(b"") == ""
    assert encoding.convert_bytes_to_hex(b"\x00\xff") == r"\x00\xff"
    assert encoding.convert_bytes_to_hex(b"A") == r"\x41"


def test_base64_roundtrip() -> None:
    """Verify roundtrip conversion to base64 and back to bytes."""

    original = b"declusor security payload test \x00\xff\xfe"
    b64 = encoding.convert_to_base64(original)
    decoded = encoding.convert_base64_to_bytes(b64)
    assert decoded == original


def test_base64_from_string() -> None:
    """Verify base64 encoding from str input."""

    b64 = encoding.convert_to_base64("hello")
    assert b64 == "aGVsbG8="
    assert encoding.convert_base64_to_bytes(b64) == b"hello"


def test_hashing_functions() -> None:
    """Verify md5, sha256, sha384, and sha512 output matches hashlib digests."""

    data = b"test payload"
    assert encoding.hash_md5(data) == hashlib.md5(data).digest()
    assert encoding.hash_sha256(data) == hashlib.sha256(data).digest()
    assert encoding.hash_sha384(data) == hashlib.sha384(data).digest()
    assert encoding.hash_sha512(data) == hashlib.sha512(data).digest()
    assert encoding.hash_sha256("test payload") == hashlib.sha256(data).digest()


def test_xor_bytes_roundtrip() -> None:
    """Verify XOR encoding and decoding returns the original data."""

    data = b"Hello, Declusor Transport Protocol!"
    key = b"secret_key_123"

    encrypted = encoding.xor_bytes(data, key)
    assert encrypted != data

    decrypted = encoding.xor_bytes(encrypted, key)
    assert decrypted == data


def test_xor_bytes_empty_data() -> None:
    """Verify XOR on empty bytes returns empty bytes."""

    assert encoding.xor_bytes(b"", b"key") == b""


def test_xor_bytes_empty_key_raises_error() -> None:
    """Verify ValueError is raised if key is empty."""

    import pytest

    with pytest.raises(ValueError, match="XOR key cannot be empty"):
        encoding.xor_bytes(b"data", b"")


def test_xor_bytes_negative_offset_raises_error() -> None:
    """Verify ValueError is raised if offset is negative."""

    import pytest

    with pytest.raises(ValueError, match="Offset cannot be negative"):
        encoding.xor_bytes(b"data", b"key", offset=-1)


def test_xor_bytes_stream_fragmentation_with_offset() -> None:
    """Verify chunked encryption with offset matches contiguous stream encryption."""

    full_payload = b"A" * 50 + b"B" * 50 + b"C" * 50
    key = b"cyclic_key"

    contiguous = encoding.xor_bytes(full_payload, key)

    chunk1 = encoding.xor_bytes(full_payload[:40], key, offset=0)
    chunk2 = encoding.xor_bytes(full_payload[40:110], key, offset=40)
    chunk3 = encoding.xor_bytes(full_payload[110:], key, offset=110)

    assert chunk1 + chunk2 + chunk3 == contiguous
