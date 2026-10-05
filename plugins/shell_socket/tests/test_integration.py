import base64
import subprocess

import declusor_shell_socket as shell_socket

from declusor import config, contract, transport


class TestShellSocketIntegration:
    """End-to-end integration tests spawning native shell_socket reverse clients."""

    def test_shell_socket__handshake_and_command_execution__succeeds(self) -> None:
        """Verify shell_socket launcher connects, completes handshake, and executes commands."""

        listener = transport.TcpListener("127.0.0.1", 0)
        port = listener.port

        options = shell_socket.ShellSocketPlugin.extract_options({})
        plugin_config = shell_socket.ShellSocketPlugin.build_config("127.0.0.1", port, options)
        runtime = shell_socket.ShellSocketPlugin.build_runtime(plugin_config)

        proc = subprocess.Popen(["bash", "-c", runtime.launcher.wrapped_text])
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

            b64_script = base64.b64encode(b"echo in_memory_script_works").decode()
            rendered = connection.renderer.render_operation_command(config.OperationCode.EXEC_FILE, b64_script)
            assert rendered is not None
            connection.write(f"{rendered}\n".encode())
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

    def test_shell_socket__resilience__handles_empty_and_special_characters(self) -> None:
        """Verify shell_socket recovers from empty inputs, trailing spaces, and quotes."""

        listener = transport.TcpListener("127.0.0.1", 0)
        port = listener.port

        options = shell_socket.ShellSocketPlugin.extract_options({})
        plugin_config = shell_socket.ShellSocketPlugin.build_config("127.0.0.1", port, options)
        runtime = shell_socket.ShellSocketPlugin.build_runtime(plugin_config)

        proc = subprocess.Popen(["bash", "-c", runtime.launcher.wrapped_text])
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
            rendered = connection.renderer.render_operation_command(config.OperationCode.EXEC_FILE, b64_script)
            assert rendered is not None
            connection.write(f"{rendered}\n".encode())
            response = b"".join(connection.read())
            assert b"resilient_shell" in response

            connection.close()
        finally:
            if raw_transport is not None:
                raw_transport.close()
            listener.close()
            proc.kill()
            proc.wait(timeout=5.0)

    def test_shell_socket__stdin_isolation__commands_reading_stdin_do_not_hang_or_desync(self) -> None:
        """Verify commands reading from standard input receive EOF without hanging or stealing socket frames."""

        listener = transport.TcpListener("127.0.0.1", 0)
        port = listener.port

        options = shell_socket.ShellSocketPlugin.extract_options({})
        plugin_config = shell_socket.ShellSocketPlugin.build_config("127.0.0.1", port, options)
        runtime = shell_socket.ShellSocketPlugin.build_runtime(plugin_config)

        proc = subprocess.Popen(["bash", "-c", runtime.launcher.wrapped_text])
        raw_transport: contract.ITransport | None = None

        try:
            raw_transport = listener.accept(timeout=5.0)
            connection = runtime.create_connection(raw_transport)
            connection.handshake()

            # Commands like 'cat' without args would hang forever in unshielded reverse shells
            connection.write(b"cat\n")
            response = b"".join(connection.read())
            assert response == b""

            # Subsequent commands must execute without desynchronization
            connection.write(b"echo post_cat_alive\n")
            response = b"".join(connection.read())
            assert b"post_cat_alive" in response

            connection.close()
        finally:
            if raw_transport is not None:
                raw_transport.close()
            listener.close()
            proc.kill()
            proc.wait(timeout=5.0)
