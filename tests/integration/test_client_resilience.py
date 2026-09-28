import base64
import subprocess
import sys

from declusor import contract, core, transport


def test_shell_socket_resilience_empty_and_special_chars() -> None:
    """Verify shell_socket recovers from empty inputs, trailing spaces, and quotes."""

    listener = transport.TcpListener("127.0.0.1", 0)
    port = listener.port

    manager = core.PluginManager().discover()
    plugin_class = manager.get("shell_socket")
    options = plugin_class.extract_options({})
    config = plugin_class.build_config("127.0.0.1", port, options)
    runtime = plugin_class.build_runtime(config)

    proc = subprocess.Popen(["bash", "-c", runtime.launcher])
    raw_transport: contract.ITransport | None = None

    try:
        raw_transport = listener.accept(timeout=5.0)
        connection = runtime.create_connection(raw_transport)
        connection.handshake()

        # Repeated empty inputs must not terminate the shell
        connection.write(b"")
        assert b"".join(connection.read()) == b""

        connection.write(b"   \n")
        assert b"".join(connection.read()) == b""

        # Special characters and quote escaping
        connection.write(b"echo 'special $PATH & \"quotes\"'\n")
        response = b"".join(connection.read())
        assert b'special $PATH & "quotes"' in response

        # In-memory execution without touching disk
        b64_script = base64.b64encode(b"VAR='resilient_shell'; echo $VAR").decode()
        connection.write(f"execute_base64_encoded_value {b64_script}\n".encode())
        response = b"".join(connection.read())
        assert b"resilient_shell" in response

        connection.close()
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

    manager = core.PluginManager().discover()
    plugin_class = manager.get("py_socket")
    options = plugin_class.extract_options({})
    config = plugin_class.build_config("127.0.0.1", port, options)
    runtime = plugin_class.build_runtime(config)

    proc = subprocess.Popen([sys.executable, "-c", runtime.launcher])
    raw_transport: contract.ITransport | None = None

    try:
        raw_transport = listener.accept(timeout=5.0)
        connection = runtime.create_connection(raw_transport)
        connection.handshake()

        # Trigger SystemExit
        connection.write(b"import sys\nsys.exit(42)\n")
        response = b"".join(connection.read())
        assert b"[py_socket error] SystemExit: 42" in response
        assert connection.last_exit_code == 42

        # Verify client is still running and receptive
        connection.write(b"print('agent_still_alive')\n")
        response = b"".join(connection.read())
        assert b"agent_still_alive" in response
        assert connection.last_exit_code == 0

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

    manager = core.PluginManager().discover()
    plugin_class = manager.get("py_socket")
    options = plugin_class.extract_options({})
    config = plugin_class.build_config("127.0.0.1", port, options)
    runtime = plugin_class.build_runtime(config)

    proc = subprocess.Popen([sys.executable, "-c", runtime.launcher])
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

    manager = core.PluginManager().discover()
    plugin_class = manager.get("py_socket")
    options = plugin_class.extract_options({})
    config = plugin_class.build_config("127.0.0.1", port, options)
    runtime = plugin_class.build_runtime(config)

    proc = subprocess.Popen([sys.executable, "-c", runtime.launcher])
    raw_transport: contract.ITransport | None = None

    try:
        raw_transport = listener.accept(timeout=5.0)
        connection = runtime.create_connection(raw_transport)
        connection.handshake()

        # Command that outputs distinct lines
        cmd = b"echo stream_chunk_1; echo stream_chunk_2; echo stream_chunk_3\n"
        connection.write(cmd)

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
