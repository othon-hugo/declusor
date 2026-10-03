import subprocess
import sys

import declusor_py_socket as py_socket

from declusor import config, contract, transport


def test_py_socket_handshake_and_command_execution() -> None:
    """Verify py_socket launcher connects, completes handshake, and executes commands."""

    listener = transport.TcpListener("127.0.0.1", 0)
    port = listener.port

    options = py_socket.PySocketPlugin.extract_options({})
    plugin_config = py_socket.PySocketPlugin.build_config("127.0.0.1", port, options)
    runtime = py_socket.PySocketPlugin.build_runtime(plugin_config)

    proc = subprocess.Popen([sys.executable, "-c", runtime.launcher.text])
    raw_transport: contract.ITransport | None = None

    try:
        raw_transport = listener.accept(timeout=5.0)

        connection = runtime.create_connection(raw_transport)
        state: contract.ConnectionState = connection.state
        assert state == contract.ConnectionState.CREATED

        connection.handshake()
        state = connection.state
        assert state == contract.ConnectionState.CONNECTED

        rendered_cmd = connection.profile.render_operation_command(
            config.OperationCode.EXEC_COMMAND,
            "echo py_shell_handshake_ok",
        )
        assert rendered_cmd is not None
        connection.write(rendered_cmd.encode())
        response = b"".join(connection.read())
        assert b"py_shell_handshake_ok" in response

        rendered_py = connection.profile.render_operation_command(
            config.OperationCode.EXEC_CODE,
            "#!/usr/bin/env python\nprint('py_native_ok')\n",
        )
        assert rendered_py is not None
        connection.write(rendered_py.encode())
        response = b"".join(connection.read())
        assert b"py_native_ok" in response

        connection.close()
        state = connection.state
        assert state == contract.ConnectionState.CLOSED
    finally:
        if raw_transport is not None:
            raw_transport.close()

        listener.close()
        proc.kill()
        proc.wait(timeout=5.0)


def test_py_socket_resilience_sys_exit_trap() -> None:
    """Verify py_socket catches sys.exit() and preserves the reverse shell agent."""

    listener = transport.TcpListener("127.0.0.1", 0)
    port = listener.port

    options = py_socket.PySocketPlugin.extract_options({})
    plugin_config = py_socket.PySocketPlugin.build_config("127.0.0.1", port, options)
    runtime = py_socket.PySocketPlugin.build_runtime(plugin_config)

    proc = subprocess.Popen([sys.executable, "-c", runtime.launcher.text])
    raw_transport: contract.ITransport | None = None

    try:
        raw_transport = listener.accept(timeout=5.0)
        connection = runtime.create_connection(raw_transport)
        connection.handshake()

        # Trigger SystemExit
        connection.write(b"import sys\nsys.exit(42)\n")
        response = b"".join(connection.read())
        assert b"[py_socket error] SystemExit: 42" in response

        # Verify client is still running and receptive
        connection.write(b"print('agent_still_alive')\n")
        response = b"".join(connection.read())
        assert b"agent_still_alive" in response

        connection.close()
    finally:
        if raw_transport is not None:
            raw_transport.close()
        listener.close()
        proc.kill()
        proc.wait(timeout=5.0)


def test_py_socket_resilience_comments_and_docstrings() -> None:
    """Verify py_socket executes scripts starting with comments and docstrings in-memory."""

    listener = transport.TcpListener("127.0.0.1", 0)
    port = listener.port

    options = py_socket.PySocketPlugin.extract_options({})
    plugin_config = py_socket.PySocketPlugin.build_config("127.0.0.1", port, options)
    runtime = py_socket.PySocketPlugin.build_runtime(plugin_config)

    proc = subprocess.Popen([sys.executable, "-c", runtime.launcher.text])
    raw_transport: contract.ITransport | None = None

    try:
        raw_transport = listener.accept(timeout=5.0)
        connection = runtime.create_connection(raw_transport)
        connection.handshake()

        script = (
            "# File: test_script.py\n"
            "# Description: testing comments\n"
            '"""\n'
            "Module docstring\n"
            '"""\n'
            "import os\n"
            'result = f"python_pid_{os.getpid()}"\n'
            "print(result)\n"
        )

        connection.write(script.encode())
        response = b"".join(connection.read())
        assert b"python_pid_" in response

        connection.close()
    finally:
        if raw_transport is not None:
            raw_transport.close()
        listener.close()
        proc.kill()
        proc.wait(timeout=5.0)


def test_py_socket_resilience_realtime_streaming() -> None:
    """Verify py_socket streams subprocess command output without deadlocking or buffering all."""

    listener = transport.TcpListener("127.0.0.1", 0)
    port = listener.port

    options = py_socket.PySocketPlugin.extract_options({})
    plugin_config = py_socket.PySocketPlugin.build_config("127.0.0.1", port, options)
    runtime = py_socket.PySocketPlugin.build_runtime(plugin_config)

    proc = subprocess.Popen([sys.executable, "-c", runtime.launcher.text])
    raw_transport: contract.ITransport | None = None

    try:
        raw_transport = listener.accept(timeout=5.0)
        connection = runtime.create_connection(raw_transport)
        connection.handshake()

        # Command that outputs distinct lines rendered via connection profile
        raw_cmd = "echo stream_chunk_1; echo stream_chunk_2; echo stream_chunk_3\n"
        rendered = connection.profile.render_operation_command(
            config.OperationCode.EXEC_COMMAND,
            raw_cmd,
        )
        assert rendered is not None
        connection.write(rendered.encode())

        chunks = list(connection.read())
        combined = b"".join(chunks)

        assert b"stream_chunk_1" in combined
        assert b"stream_chunk_2" in combined
        assert b"stream_chunk_3" in combined

        connection.close()
    finally:
        if raw_transport is not None:
            raw_transport.close()

        listener.close()

        proc.kill()
        proc.wait(timeout=5.0)
