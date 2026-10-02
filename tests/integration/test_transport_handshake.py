import subprocess
import sys

from declusor import config, contract, core, transport


def test_shell_socket_handshake_and_command_execution() -> None:
    """Verify shell_socket launcher connects, completes handshake, and executes commands."""

    listener = transport.TcpListener("127.0.0.1", 0)
    port = listener.port

    manager = core.PluginManager().discover()
    plugin_class = manager.get("shell_socket")
    options = plugin_class.extract_options({})
    config = plugin_class.build_config("127.0.0.1", port, options)
    runtime = plugin_class.build_runtime(config)

    proc = subprocess.Popen(["bash", "-c", runtime.launcher.text])
    raw_transport: contract.ITransport | None = None

    try:
        raw_transport = listener.accept(timeout=5.0)

        connection = runtime.create_connection(raw_transport)
        state: contract.ConnectionState = connection.state
        assert state == contract.ConnectionState.CREATED

        connection.handshake()
        state = connection.state
        assert state == contract.ConnectionState.CONNECTED

        connection.write(b"echo shell_handshake_ok\n")
        response = b"".join(connection.read())
        assert b"shell_handshake_ok" in response

        connection.write(b"")
        response = b"".join(connection.read())
        assert response == b""

        connection.write(b"echo shell_still_alive\n")
        response = b"".join(connection.read())
        assert b"shell_still_alive" in response

        import base64

        b64_script = base64.b64encode(b"echo in_memory_script_works").decode()
        connection.write(f"execute_base64_encoded_value {b64_script}\n".encode())
        response = b"".join(connection.read())
        assert b"in_memory_script_works" in response

        connection.close()
        state = connection.state
        assert state == contract.ConnectionState.CLOSED
    finally:
        if raw_transport is not None:
            raw_transport.close()

        listener.close()
        proc.kill()
        proc.wait(timeout=5.0)


def test_py_socket_handshake_and_command_execution() -> None:
    """Verify py_socket launcher connects, completes handshake, and executes commands."""

    listener = transport.TcpListener("127.0.0.1", 0)
    port = listener.port

    manager = core.PluginManager().discover()
    plugin_class = manager.get("py_socket")
    options = plugin_class.extract_options({})
    plugin_config = plugin_class.build_config("127.0.0.1", port, options)
    runtime = plugin_class.build_runtime(plugin_config)

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
