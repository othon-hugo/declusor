import binascii
import hashlib

import pytest

from declusor.util import encoding


class TestQuote:
    """Verify shell token quoting and escaping behavior."""

    def test_quote__already_safe_token__returns_unquoted_string(self) -> None:
        """Verify safe alphanumeric strings are left unquoted."""

        assert encoding.quote("hello_world-123/path.txt") == "hello_world-123/path.txt"

    def test_quote__whitespace_in_token__returns_single_quoted_string(self) -> None:
        """Verify strings containing spaces or tabs are safely wrapped in quotes."""

        assert encoding.quote("hello world") == "'hello world'"
        assert encoding.quote("column\tvalue") == "'column\tvalue'"

    def test_quote__shell_metacharacters__escapes_command_injection(self) -> None:
        """Verify shell control characters and command chains are neutralised."""

        assert encoding.quote("a; rm -rf /") == "'a; rm -rf /'"
        assert encoding.quote("$(whoami)") == "'$(whoami)'"
        assert encoding.quote("foo | bar & baz > out") == "'foo | bar & baz > out'"

    def test_quote__empty_string__returns_empty_single_quotes(self) -> None:
        """Verify empty string is represented as empty single-quoted token."""

        assert encoding.quote("") == "''"

    def test_quote__unicode_characters__escapes_properly(self) -> None:
        """Verify strings with unicode and emoji symbols are properly quoted."""

        assert encoding.quote("olá mundo") == "'olá mundo'"
        assert encoding.quote("rocket 🚀 test") == "'rocket 🚀 test'"


class TestFormatTemplate:
    """Verify template string substitution and escaping."""

    def test_format_template__matching_keys__substitutes_values(self) -> None:
        """Verify matching keys replace standard dollar placeholders."""

        template = "HOST=$HOST PORT=$PORT"
        result = encoding.format_template(template, HOST="127.0.0.1", PORT="8080")

        assert result == "HOST=127.0.0.1 PORT=8080"

    def test_format_template__integer_values__converts_and_substitutes(self) -> None:
        """Verify integer keyword arguments are converted and formatted."""

        template = "listen 0.0.0.0:$PORT count=$COUNT"
        result = encoding.format_template(template, PORT=4444, COUNT=10)

        assert result == "listen 0.0.0.0:4444 count=10"

    def test_format_template__braced_placeholders__substitutes_values(self) -> None:
        """Verify braced placeholders like ${NAME} are substituted correctly."""

        template = "prefix_${NAME}_suffix"
        result = encoding.format_template(template, NAME="core")

        assert result == "prefix_core_suffix"

    def test_format_template__missing_keys__preserves_unmatched_placeholders(self) -> None:
        """Verify safe_substitute retains placeholders when key is omitted."""

        template = "KNOWN=$KNOWN UNKNOWN=$UNKNOWN"
        result = encoding.format_template(template, KNOWN="yes")

        assert result == "KNOWN=yes UNKNOWN=$UNKNOWN"

    def test_format_template__escaped_dollar__preserves_literal_dollar(self) -> None:
        """Verify double dollar signs produce a literal dollar sign."""

        template = "$$COST=$AMOUNT"
        result = encoding.format_template(template, AMOUNT=50)

        assert result == "$COST=50"

    def test_format_template__empty_template__returns_empty_string(self) -> None:
        """Verify empty template string returns an empty string."""

        assert encoding.format_template("", KEY="val") == ""


class TestConvertToBytes:
    """Verify string and bytes conversion to UTF-8 bytes."""

    def test_convert_to_bytes__ascii_string__encodes_utf8_bytes(self) -> None:
        """Verify ASCII string is converted to UTF-8 bytes."""

        assert encoding.convert_to_bytes("hello") == b"hello"

    def test_convert_to_bytes__unicode_string__encodes_multibyte_utf8(self) -> None:
        """Verify unicode string with accents and emojis encodes to multibyte bytes."""

        assert encoding.convert_to_bytes("café 🚀") == "café 🚀".encode()

    def test_convert_to_bytes__bytes_input__returns_identical_bytes(self) -> None:
        """Verify bytes input is returned as identical byte sequence without modification."""

        raw = b"\x00\xff\xfe\xca\xfe"
        result = encoding.convert_to_bytes(raw)

        assert result == raw
        assert isinstance(result, bytes)

    def test_convert_to_bytes__empty_string__returns_empty_bytes(self) -> None:
        """Verify empty string converts to empty bytes."""

        assert encoding.convert_to_bytes("") == b""

    def test_convert_to_bytes__empty_bytes__returns_empty_bytes(self) -> None:
        """Verify empty bytes returns empty bytes."""

        assert encoding.convert_to_bytes(b"") == b""


class TestConvertBytesToHex:
    """Verify byte formatting to escaped hex string representations."""

    def test_convert_bytes_to_hex__empty_bytes__returns_empty_string(self) -> None:
        """Verify empty bytes input produces an empty string."""

        assert encoding.convert_bytes_to_hex(b"") == ""

    def test_convert_bytes_to_hex__single_digits__zero_pads_hex_escape(self) -> None:
        """Verify hex formatting zero-pads single-digit byte values with \\x prefix."""

        assert encoding.convert_bytes_to_hex(b"\x00\x05\x0a\x0f") == r"\x00\x05\x0a\x0f"

    def test_convert_bytes_to_hex__boundary_bytes__formats_null_and_max_byte(self) -> None:
        """Verify boundary bytes 0x00 and 0xFF format properly."""

        assert encoding.convert_bytes_to_hex(b"\x00\xff") == r"\x00\xff"

    def test_convert_bytes_to_hex__ascii_bytes__formats_hex_escapes(self) -> None:
        """Verify ASCII characters are formatted as escaped hex values."""

        assert encoding.convert_bytes_to_hex(b"ABC") == r"\x41\x42\x43"


class TestConvertToBase64:
    """Verify Base64 encoding from string and bytes."""

    def test_convert_to_base64__string_input__encodes_base64_string(self) -> None:
        """Verify string input is encoded to standard Base64 string."""

        assert encoding.convert_to_base64("hello") == "aGVsbG8="

    def test_convert_to_base64__bytes_input__encodes_base64_string(self) -> None:
        """Verify bytes input is encoded directly to Base64 string."""

        assert encoding.convert_to_base64(b"hello") == "aGVsbG8="

    def test_convert_to_base64__empty_input__returns_empty_string(self) -> None:
        """Verify empty string and empty bytes produce empty Base64 string."""

        assert encoding.convert_to_base64("") == ""
        assert encoding.convert_to_base64(b"") == ""

    def test_convert_to_base64__rfc4648_test_vectors__produces_correct_padding(self) -> None:
        """Verify standard RFC 4648 vectors with 0, 1, and 2 pad characters."""

        assert encoding.convert_to_base64("f") == "Zg=="
        assert encoding.convert_to_base64("fo") == "Zm8="
        assert encoding.convert_to_base64("foo") == "Zm9v"

    def test_convert_to_base64__binary_payload_with_nulls__encodes_accurately(self) -> None:
        """Verify binary payloads containing null bytes encode faithfully."""

        binary = b"\x00\x01\x02\xfe\xff"
        assert encoding.convert_to_base64(binary) == "AAEC/v8="


class TestConvertBase64ToBytes:
    """Verify Base64 decoding into raw bytes."""

    def test_convert_base64_to_bytes__valid_base64__decodes_original_bytes(self) -> None:
        """Verify standard Base64 string decodes to original bytes."""

        assert encoding.convert_base64_to_bytes("aGVsbG8=") == b"hello"
        assert encoding.convert_base64_to_bytes("Zm9v") == b"foo"

    def test_convert_base64_to_bytes__empty_string__returns_empty_bytes(self) -> None:
        """Verify empty string decodes to empty bytes."""

        assert encoding.convert_base64_to_bytes("") == b""

    def test_convert_base64_to_bytes__whitespace_and_newlines__ignores_whitespace(self) -> None:
        """Verify Base64 strings with spaces or line breaks decode cleanly."""

        assert encoding.convert_base64_to_bytes("aGVs\nbG8=\n") == b"hello"

    def test_convert_base64_to_bytes__invalid_characters__raises_error(self) -> None:
        """Verify malformed Base64 string with invalid characters raises binascii.Error."""

        with pytest.raises((binascii.Error, ValueError)):
            encoding.convert_base64_to_bytes("!not-valid-base64!")


class TestHashMd5:
    """Verify MD5 hash calculations."""

    def test_hash_md5__bytes_input__returns_16_byte_digest(self) -> None:
        """Verify hash_md5 on bytes returns 16-byte digest matching hashlib."""

        data = b"declusor MD5 test vector"
        digest = encoding.hash_md5(data)

        assert len(digest) == 16
        assert digest == hashlib.md5(data).digest()

    def test_hash_md5__string_input__matches_bytes_digest(self) -> None:
        """Verify hash_md5 produces identical digest for string and encoded bytes."""

        text = "consistent payload"
        assert encoding.hash_md5(text) == encoding.hash_md5(text.encode())

    def test_hash_md5__empty_input__returns_known_empty_md5_digest(self) -> None:
        """Verify hash_md5 on empty input matches standard empty MD5 digest."""

        expected = bytes.fromhex("d41d8cd98f00b204e9800998ecf8427e")
        assert encoding.hash_md5(b"") == expected
        assert encoding.hash_md5("") == expected


class TestHashSha256:
    """Verify SHA-256 hash calculations."""

    def test_hash_sha256__bytes_input__returns_32_byte_digest(self) -> None:
        """Verify hash_sha256 on bytes returns 32-byte digest matching hashlib."""

        data = b"declusor SHA256 test vector"
        digest = encoding.hash_sha256(data)

        assert len(digest) == 32
        assert digest == hashlib.sha256(data).digest()

    def test_hash_sha256__string_input__matches_bytes_digest(self) -> None:
        """Verify hash_sha256 produces identical digest for string and encoded bytes."""

        text = "consistent sha256 payload"
        assert encoding.hash_sha256(text) == encoding.hash_sha256(text.encode())

    def test_hash_sha256__empty_input__returns_known_empty_sha256_digest(self) -> None:
        """Verify hash_sha256 on empty input matches standard empty SHA256 digest."""

        expected = bytes.fromhex("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        assert encoding.hash_sha256(b"") == expected
        assert encoding.hash_sha256("") == expected


class TestHashSha384:
    """Verify SHA-384 hash calculations."""

    def test_hash_sha384__bytes_input__returns_48_byte_digest(self) -> None:
        """Verify hash_sha384 on bytes returns 48-byte digest matching hashlib."""

        data = b"declusor SHA384 test vector"
        digest = encoding.hash_sha384(data)

        assert len(digest) == 48
        assert digest == hashlib.sha384(data).digest()

    def test_hash_sha384__string_input__matches_bytes_digest(self) -> None:
        """Verify hash_sha384 produces identical digest for string and encoded bytes."""

        text = "consistent sha384 payload"
        assert encoding.hash_sha384(text) == encoding.hash_sha384(text.encode())

    def test_hash_sha384__empty_input__returns_known_empty_sha384_digest(self) -> None:
        """Verify hash_sha384 on empty input matches standard empty SHA384 digest."""

        expected = hashlib.sha384(b"").digest()
        assert encoding.hash_sha384(b"") == expected
        assert encoding.hash_sha384("") == expected


class TestHashSha512:
    """Verify SHA-512 hash calculations."""

    def test_hash_sha512__bytes_input__returns_64_byte_digest(self) -> None:
        """Verify hash_sha512 on bytes returns 64-byte digest matching hashlib."""

        data = b"declusor SHA512 test vector"
        digest = encoding.hash_sha512(data)

        assert len(digest) == 64
        assert digest == hashlib.sha512(data).digest()

    def test_hash_sha512__string_input__matches_bytes_digest(self) -> None:
        """Verify hash_sha512 produces identical digest for string and encoded bytes."""

        text = "consistent sha512 payload"
        assert encoding.hash_sha512(text) == encoding.hash_sha512(text.encode())

    def test_hash_sha512__empty_input__returns_known_empty_sha512_digest(self) -> None:
        """Verify hash_sha512 on empty input matches standard empty SHA512 digest."""

        expected = hashlib.sha512(b"").digest()
        assert encoding.hash_sha512(b"") == expected
        assert encoding.hash_sha512("") == expected


class TestXorBytes:
    """Verify repeating-key XOR encryption and stream offsetting."""

    def test_xor_bytes__roundtrip__restores_original_data(self) -> None:
        """Verify repeating-key XOR encryption and decryption restores plaintext."""

        data = b"Hello, Declusor Transport Protocol!"
        key = b"secret_key_123"

        encrypted = encoding.xor_bytes(data, key)
        assert encrypted != data

        decrypted = encoding.xor_bytes(encrypted, key)
        assert decrypted == data

    def test_xor_bytes__empty_data__returns_empty_bytes(self) -> None:
        """Verify XOR operation on empty byte sequence returns empty bytes."""

        assert encoding.xor_bytes(b"", b"key") == b""
        assert encoding.xor_bytes(b"", b"key", offset=10) == b""

    def test_xor_bytes__empty_key__raises_value_error(self) -> None:
        """Verify ValueError is raised if key is empty."""

        with pytest.raises(ValueError, match="XOR key cannot be empty"):
            encoding.xor_bytes(b"data", b"")

    def test_xor_bytes__negative_offset__raises_value_error(self) -> None:
        """Verify ValueError is raised if offset is negative."""

        with pytest.raises(ValueError, match="Offset cannot be negative"):
            encoding.xor_bytes(b"data", b"key", offset=-1)

    def test_xor_bytes__offset_within_key__shifts_keystream(self) -> None:
        """Verify non-zero offset begins encryption from the shifted key byte."""

        data = b"AAAA"
        key = b"ABCD"

        # offset 0 uses key ABCD
        res_0 = encoding.xor_bytes(data, key, offset=0)
        # offset 1 uses key BCDA
        res_1 = encoding.xor_bytes(data, key, offset=1)

        assert res_0 == bytes([ord("A") ^ ord("A"), ord("A") ^ ord("B"), ord("A") ^ ord("C"), ord("A") ^ ord("D")])
        assert res_1 == bytes([ord("A") ^ ord("B"), ord("A") ^ ord("C"), ord("A") ^ ord("D"), ord("A") ^ ord("A")])

    def test_xor_bytes__offset_exceeding_key_length__wraps_keystream_correctly(self) -> None:
        """Verify offset values greater than key length wrap around modulo key length."""

        data = b"test payload"
        key = b"key"

        res_1 = encoding.xor_bytes(data, key, offset=1)
        res_wrap = encoding.xor_bytes(data, key, offset=1 + len(key) * 5)

        assert res_1 == res_wrap

    def test_xor_bytes__single_byte_key__applies_uniform_mask(self) -> None:
        """Verify single-byte key applies identical mask regardless of offset."""

        data = b"\x00\x01\x02\x03"
        key = b"\xff"

        result = encoding.xor_bytes(data, key, offset=5)
        assert result == b"\xff\xfe\xfd\xfc"

    def test_xor_bytes__key_longer_than_data__uses_prefix_of_key(self) -> None:
        """Verify keystream uses only necessary prefix when key is longer than data."""

        data = b"hi"
        key = b"superlongkey"

        result = encoding.xor_bytes(data, key)
        assert result == bytes([ord("h") ^ ord("s"), ord("i") ^ ord("u")])

    def test_xor_bytes__stream_fragmentation__matches_contiguous_ciphertext(self) -> None:
        """Verify chunked encryption with continuous offset matches contiguous encryption."""

        full_payload = b"X" * 33 + b"Y" * 44 + b"Z" * 55
        key = b"fragmentation_key"

        contiguous = encoding.xor_bytes(full_payload, key)

        chunk1 = encoding.xor_bytes(full_payload[:33], key, offset=0)
        chunk2 = encoding.xor_bytes(full_payload[33:77], key, offset=33)
        chunk3 = encoding.xor_bytes(full_payload[77:], key, offset=77)

        assert chunk1 + chunk2 + chunk3 == contiguous
