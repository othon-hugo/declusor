"""Helper library: file operations for the py_socket client agent.

This module is transmitted to the remote Python agent during the session
initialization handshake and executed in the persistent session scope.
Once loaded, all functions are available to any subsequent module or command.

All functions use only the Python standard library to maintain zero-dependency
compatibility with any Python 3.6+ environment.
"""

import base64
import hashlib
import os
import subprocess
import sys
import tempfile


def hash_value(data: str | bytes) -> str:
    """Compute the SHA-256 hex digest of the given data.

    Args:
        data: The string or bytes to hash.

    Returns:
        Lowercase hexadecimal SHA-256 digest string.
    """

    if isinstance(data, str):
        data = data.encode()

    return hashlib.sha256(data).hexdigest()


def store_base64_encoded_value(data_b64: str, target_path: str = "") -> str:
    """Decode a Base64-encoded string and write it to disk.

    Args:
        data_b64: Base64-encoded file content.
        target_path: Destination path for the decoded file. When empty,
            a deterministic temporary file is created under the system
            temporary directory using the SHA-256 hash of the content.

    Returns:
        Absolute path of the file that was written.

    Raises:
        ValueError: If ``data_b64`` is empty or cannot be decoded.
        OSError: If the file cannot be written to the target location.
    """

    if not data_b64:
        raise ValueError("data_b64 must not be empty.")

    raw_bytes = base64.b64decode(data_b64)

    if not target_path:
        content_hash = hash_value(raw_bytes)
        target_path = os.path.join(tempfile.gettempdir(), f"{content_hash}.temp")

    with open(target_path, "wb") as fh:
        fh.write(raw_bytes)

    return target_path


def execute_base64_encoded_value(data_b64: str, *args: str) -> None:
    """Decode a Base64-encoded payload and execute it on the remote agent.

    Chooses the execution strategy based on the decoded content:

    - **Python in-memory execution** (``exec``): When the payload begins with
      a Python shebang (``#!/usr/bin/env python``), a ``#!python`` marker, or
      when the first non-blank line starts with a Python keyword (``import``,
      ``def``, ``class``). This avoids writing anything to disk.
    - **Subprocess execution**: For shell scripts or arbitrary binaries. The
      decoded content is written to a deterministic temporary file, the file
      is made executable, executed via ``subprocess.run``, and then removed.

    Args:
        data_b64: Base64-encoded payload to execute.
        *args: Additional arguments forwarded to subprocess execution.

    Raises:
        ValueError: If ``data_b64`` is empty.
        OSError: If a temporary file cannot be created or executed.
    """

    if not data_b64:
        raise ValueError("data_b64 must not be empty.")

    raw_bytes = base64.b64decode(data_b64)

    if _is_python_payload(raw_bytes):
        code = raw_bytes.decode(errors="replace")
        exec(code, globals())  # noqa: S102
        return

    filepath = store_base64_encoded_value(data_b64)

    try:
        os.chmod(filepath, 0o700)
        subprocess.run([filepath, *args], check=False)  # noqa: S603
    finally:
        with suppress(OSError):
            os.remove(filepath)


def _is_python_payload(raw_bytes: bytes) -> bool:
    """Return True if the decoded payload appears to be Python source code."""

    try:
        first_line = raw_bytes.lstrip().split(b"\n", 1)[0].strip().lower()
    except Exception:  # noqa: BLE001
        return False

    python_markers = (b"#!/usr/bin/env python", b"#!/usr/bin/python", b"#!python")
    if any(first_line.startswith(m) for m in python_markers):
        return True

    python_keywords = (b"import ", b"from ", b"def ", b"class ", b"async def ")
    return any(first_line.startswith(k) for k in python_keywords)


try:
    from contextlib import suppress
except ImportError:
    from contextlib import contextmanager

    @contextmanager
    def suppress(*exceptions):
        try:
            yield
        except exceptions:
            pass
