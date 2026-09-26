import socket
import subprocess
import sys

from declusor import contract, main


def test_shell_socket_handshake_and_command_execution() -> None:
    """Verify shell_socket launcher connects, completes handshake, and executes commands."""

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    port = server.getsockname()[1]
    server.listen(1)
    server.settimeout(5.0)

    app = main.create_application()

    Plugin = app.manager.get("shell_socket")
    config = Plugin.build_config(contract.PluginNamespace(host="127.0.0.1", port=port))
    runtime = Plugin.build_runtime(config)

    proc = subprocess.Popen(["bash", "-c", runtime.client_script])
    client_conn: socket.socket | None = None

    try:
        raw_conn, _ = server.accept()
        raw_conn.settimeout(5.0)
        client_conn = raw_conn

        connection = runtime.create_connection(raw_conn)
        state: contract.ConnectionState = connection.state
        assert state == contract.ConnectionState.CREATED

        connection.initialize()
        state = connection.state
        assert state == contract.ConnectionState.CONNECTED

        connection.write(b"echo shell_handshake_ok\n")
        response = b"".join(connection.read())
        assert b"shell_handshake_ok" in response

        connection.close()
        state = connection.state
        assert state == contract.ConnectionState.CLOSED
    finally:
        if client_conn is not None:
            client_conn.close()

        server.close()
        proc.kill()
        proc.wait(timeout=5.0)


def test_py_socket_handshake_and_command_execution() -> None:
    """Verify py_socket launcher connects, completes handshake, and executes commands."""

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    port = server.getsockname()[1]
    server.listen(1)
    server.settimeout(5.0)

    app = main.create_application()

    Plugin = app.manager.get("py_socket")
    config = Plugin.build_config(contract.PluginNamespace(host="127.0.0.1", port=port))
    runtime = Plugin.build_runtime(config)

    proc = subprocess.Popen([sys.executable, "-c", runtime.client_script])
    client_conn: socket.socket | None = None

    try:
        raw_conn, _ = server.accept()
        raw_conn.settimeout(5.0)
        client_conn = raw_conn

        connection = runtime.create_connection(raw_conn)
        state: contract.ConnectionState = connection.state
        assert state == contract.ConnectionState.CREATED

        connection.initialize()
        state = connection.state
        assert state == contract.ConnectionState.CONNECTED

        connection.write(b"echo py_shell_handshake_ok\n")
        response = b"".join(connection.read())
        assert b"py_shell_handshake_ok" in response

        connection.write(b"#!/usr/bin/env python\nprint('py_native_ok')\n")
        response = b"".join(connection.read())
        assert b"py_native_ok" in response

        connection.close()
        state = connection.state
        assert state == contract.ConnectionState.CLOSED
    finally:
        if client_conn is not None:
            client_conn.close()

        server.close()
        proc.kill()
        proc.wait(timeout=5.0)
