from base64 import b64decode, b64encode
from hashlib import md5, sha256, sha384, sha512
from shlex import quote as shlex_quote


def quote(s: str) -> str:
    return shlex_quote(s)


def convert_to_bytes(data: bytes | str, /) -> bytes:
    """Converts a string to bytes using UTF-8 encoding, or returns the input if it's already bytes.

    Args:
        data: The string or bytes object to convert.

    Returns:
        The bytes representation of the input.
    """

    return data.encode() if isinstance(data, str) else data


def convert_bytes_to_hex(data: bytes, /) -> str:
    """Convert a bytes object to its hexadecimal string representation.

    Args:
        data: The bytes object to convert.

    Returns:
        The hexadecimal string representation of the bytes.
    """

    return "".join(f"\\x{i:02x}" for i in data)


def convert_to_base64(data: str | bytes, /) -> str:
    """Convert a string to its Base64 encoded representation.

    Args:
        data: The string or bytes object to convert.

    Returns:
        The Base64 encoded string.
    """

    return b64encode(data.encode() if isinstance(data, str) else data).decode()


def convert_base64_to_bytes(data: str, /) -> bytes:
    """Convert a Base64 encoded string back to its original bytes representation.

    Args:
        data: The Base64 encoded string to convert.

    Returns:
        The original bytes representation.
    """

    return b64decode(data)


def hash_md5(data: str | bytes, /) -> bytes:
    """Hashes data using MD5.

    Args:
        data: The bytes object to hash.

    Returns:
        The MD5 hash as a bytes object.
    """

    return md5(convert_to_bytes(data)).digest()


def hash_sha256(data: str | bytes, /) -> bytes:
    """Hashes data using SHA256.

    Args:
        data: The bytes object to hash.

    Returns:
        The SHA256 hash as bytes.
    """

    return sha256(convert_to_bytes(data)).digest()


def hash_sha384(data: str | bytes, /) -> bytes:
    """Hashes data using SHA384.

    Args:
        data: The bytes object to hash.

    Returns:
        The SHA384 hash as bytes.
    """

    return sha384(convert_to_bytes(data)).digest()


def hash_sha512(data: str | bytes, /) -> bytes:
    """Hashes data using SHA512.

    Args:
        data: The bytes object to hash.

    Returns:
        The SHA512 hash as bytes.
    """

    return sha512(convert_to_bytes(data)).digest()
