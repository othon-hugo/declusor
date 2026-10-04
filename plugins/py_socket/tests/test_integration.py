import base64
import shlex
import subprocess
import sys

import declusor_py_socket as py_socket

from declusor import config, contract, lang, transport, util


class TestPySocketIntegration:
    """End-to-end integration tests spawning native py_socket reverse clients."""

    @staticmethod
    def _spawn_launcher(launcher: contract.LauncherDelivery) -> subprocess.Popen[bytes]:
        """Spawn the launcher using its wrapped execution command with current test python."""

        cmd = shlex.split(launcher.wrapped_text)
        cmd[0] = sys.executable

        return subprocess.Popen(cmd)

    def test_py_socket__handshake_and_command_execution__succeeds(self) -> None:
        """Verify py_socket launcher connects, completes handshake, and executes commands."""

        listener = transport.TcpListener("127.0.0.1", 0)
        port = listener.port

        options = py_socket.PySocketPlugin.extract_options({})
        plugin_config = py_socket.PySocketPlugin.build_config("127.0.0.1", port, options)
        runtime = py_socket.PySocketPlugin.build_runtime(plugin_config)

        proc = self._spawn_launcher(runtime.launcher)
        raw_transport: contract.ITransport | None = None

        try:
            raw_transport = listener.accept(timeout=5.0)

            connection = runtime.create_connection(raw_transport)
            state: contract.ConnectionState = connection.state
            assert state == contract.ConnectionState.CREATED

            connection.handshake()
            state = connection.state
            assert state == contract.ConnectionState.CONNECTED

            rendered_cmd = connection.renderer.render_operation_command(
                config.OperationCode.EXEC_COMMAND,
                "echo py_shell_handshake_ok",
            )
            assert rendered_cmd is not None
            connection.write(rendered_cmd.encode())
            response = b"".join(connection.read())
            assert b"py_shell_handshake_ok" in response

            rendered_py = connection.renderer.render_operation_command(
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

    def test_py_socket__sys_exit_trap__preserves_reverse_shell_agent(self) -> None:
        """Verify py_socket catches sys.exit() and preserves the reverse shell agent."""

        listener = transport.TcpListener("127.0.0.1", 0)
        port = listener.port

        options = py_socket.PySocketPlugin.extract_options({})
        plugin_config = py_socket.PySocketPlugin.build_config("127.0.0.1", port, options)
        runtime = py_socket.PySocketPlugin.build_runtime(plugin_config)

        proc = self._spawn_launcher(runtime.launcher)
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

    def test_py_socket__comments_and_docstrings__executes_script_in_memory(self) -> None:
        """Verify py_socket executes scripts starting with comments and docstrings in-memory."""

        listener = transport.TcpListener("127.0.0.1", 0)
        port = listener.port

        options = py_socket.PySocketPlugin.extract_options({})
        plugin_config = py_socket.PySocketPlugin.build_config("127.0.0.1", port, options)
        runtime = py_socket.PySocketPlugin.build_runtime(plugin_config)

        proc = self._spawn_launcher(runtime.launcher)
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

    def test_py_socket__realtime_streaming__streams_subprocess_output_chunks(self) -> None:
        """Verify py_socket streams subprocess command output without deadlocking or buffering all."""

        listener = transport.TcpListener("127.0.0.1", 0)
        port = listener.port

        options = py_socket.PySocketPlugin.extract_options({})
        plugin_config = py_socket.PySocketPlugin.build_config("127.0.0.1", port, options)
        runtime = py_socket.PySocketPlugin.build_runtime(plugin_config)

        proc = self._spawn_launcher(runtime.launcher)
        raw_transport: contract.ITransport | None = None

        try:
            raw_transport = listener.accept(timeout=5.0)
            connection = runtime.create_connection(raw_transport)
            connection.handshake()

            # Command that outputs distinct lines rendered via connection renderer
            raw_cmd = "echo stream_chunk_1; echo stream_chunk_2; echo stream_chunk_3\n"
            rendered = connection.renderer.render_operation_command(
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

    def test_py_socket__marshaled_code_execution__executes_in_memory(self) -> None:
        """Verify client executes marshaled code objects transmitted directly over the transport."""

        listener = transport.TcpListener("127.0.0.1", 0)
        port = listener.port

        options = py_socket.PySocketPlugin.extract_options({})
        plugin_config = py_socket.PySocketPlugin.build_config("127.0.0.1", port, options)
        runtime = py_socket.PySocketPlugin.build_runtime(plugin_config)

        proc = self._spawn_launcher(runtime.launcher)
        raw_transport: contract.ITransport | None = None

        try:
            raw_transport = listener.accept(timeout=5.0)
            connection = runtime.create_connection(raw_transport)
            assert isinstance(connection, py_socket.PySocketConnection)
            connection.handshake()

            assert connection.is_bytecode_compatible is True

            # Compile and serialize Python code object
            payload = lang.python.compile_and_serialize("print('in_memory_bytecode_success')\n")
            connection.write(payload)

            response = b"".join(connection.read())
            assert b"in_memory_bytecode_success" in response

            connection.close()
        finally:
            if raw_transport is not None:
                raw_transport.close()
            listener.close()
            proc.kill()
            proc.wait(timeout=5.0)

    def test_py_socket__execute_bytecode__executes_without_temporary_file(self) -> None:
        """Verify execute_bytecode runs marshaled code objects in memory."""

        listener = transport.TcpListener("127.0.0.1", 0)
        port = listener.port

        options = py_socket.PySocketPlugin.extract_options({})
        plugin_config = py_socket.PySocketPlugin.build_config("127.0.0.1", port, options)
        runtime = py_socket.PySocketPlugin.build_runtime(plugin_config)

        proc = self._spawn_launcher(runtime.launcher)
        raw_transport: contract.ITransport | None = None

        try:
            raw_transport = listener.accept(timeout=5.0)
            connection = runtime.create_connection(raw_transport)
            connection.handshake()

            # Base64 encode marshaled code object
            raw_bytecode = lang.python.compile_and_serialize("print('base64_marshaled_ok')\n")
            b64_str = base64.b64encode(raw_bytecode).decode("ascii")

            cmd = f"execute_bytecode(decode_base64('{b64_str}'))"
            connection.write(cmd.encode("utf-8"))

            response = b"".join(connection.read())
            assert b"base64_marshaled_ok" in response

            connection.close()
        finally:
            if raw_transport is not None:
                raw_transport.close()
            listener.close()
            proc.kill()
            proc.wait(timeout=5.0)

    def test_py_socket__send_python_payload__succeeds(self) -> None:
        """Verify send_python_payload compiles and executes code seamlessly on client."""

        listener = transport.TcpListener("127.0.0.1", 0)
        port = listener.port

        options = py_socket.PySocketPlugin.extract_options({})
        plugin_config = py_socket.PySocketPlugin.build_config("127.0.0.1", port, options)
        runtime = py_socket.PySocketPlugin.build_runtime(plugin_config)

        proc = self._spawn_launcher(runtime.launcher)
        raw_transport: contract.ITransport | None = None

        try:
            raw_transport = listener.accept(timeout=5.0)
            connection = runtime.create_connection(raw_transport)
            assert isinstance(connection, py_socket.PySocketConnection)
            connection.handshake()

            connection.send_python_payload("print('send_python_payload_verified')\n")

            response = b"".join(connection.read())
            assert b"send_python_payload_verified" in response

            connection.close()
        finally:
            if raw_transport is not None:
                raw_transport.close()
            listener.close()
            proc.kill()
            proc.wait(timeout=5.0)

    def test_py_socket__executes_source_in_memory(self) -> None:
        """Verify Python source executes directly in memory over STDIN bus."""

        listener = transport.TcpListener("127.0.0.1", 0)
        port = listener.port

        options = py_socket.PySocketPlugin.extract_options({})
        plugin_config = py_socket.PySocketPlugin.build_config("127.0.0.1", port, options)
        runtime = py_socket.PySocketPlugin.build_runtime(plugin_config)

        proc = self._spawn_launcher(runtime.launcher)
        raw_transport: contract.ITransport | None = None

        try:
            raw_transport = listener.accept(timeout=5.0)
            connection = runtime.create_connection(raw_transport)
            assert isinstance(connection, py_socket.PySocketConnection)
            connection.handshake()

            connection.write(b"x = 21\nprint('exec_code_result:', x * 2)\n")

            response = b"".join(connection.read())
            assert b"exec_code_result: 42" in response

            connection.close()
        finally:
            if raw_transport is not None:
                raw_transport.close()
            listener.close()
            proc.kill()
            proc.wait(timeout=5.0)

    def test_py_socket__executes_marshaled_bytecode(self) -> None:
        """Verify precompiled bytecode executes directly in memory over STDIN bus."""

        listener = transport.TcpListener("127.0.0.1", 0)
        port = listener.port

        options = py_socket.PySocketPlugin.extract_options({})
        plugin_config = py_socket.PySocketPlugin.build_config("127.0.0.1", port, options)
        runtime = py_socket.PySocketPlugin.build_runtime(plugin_config)

        proc = self._spawn_launcher(runtime.launcher)
        raw_transport: contract.ITransport | None = None

        try:
            raw_transport = listener.accept(timeout=5.0)
            connection = runtime.create_connection(raw_transport)
            assert isinstance(connection, py_socket.PySocketConnection)
            connection.handshake()

            bytecode = lang.python.compile_and_serialize("print('exec_bytecode_ok')\n")
            connection.write(bytecode)

            response = b"".join(connection.read())
            assert b"exec_bytecode_ok" in response

            connection.close()
        finally:
            if raw_transport is not None:
                raw_transport.close()
            listener.close()
            proc.kill()
            proc.wait(timeout=5.0)

    def test_py_socket__executes_shell_command_via_subprocess(self) -> None:
        """Verify rendered EXEC_COMMAND executes system command via subprocess and streams output."""

        listener = transport.TcpListener("127.0.0.1", 0)
        port = listener.port

        options = py_socket.PySocketPlugin.extract_options({})
        plugin_config = py_socket.PySocketPlugin.build_config("127.0.0.1", port, options)
        runtime = py_socket.PySocketPlugin.build_runtime(plugin_config)

        proc = self._spawn_launcher(runtime.launcher)
        raw_transport: contract.ITransport | None = None

        try:
            raw_transport = listener.accept(timeout=5.0)
            connection = runtime.create_connection(raw_transport)
            assert isinstance(connection, py_socket.PySocketConnection)
            connection.handshake()

            rendered = connection.renderer.render_operation_command(
                config.OperationCode.EXEC_COMMAND,
                "echo 'channel_command_streaming_success'",
            )
            assert rendered is not None
            connection.write(rendered.encode("utf-8"))

            response = b"".join(connection.read())
            assert b"channel_command_streaming_success" in response

            connection.close()
        finally:
            if raw_transport is not None:
                raw_transport.close()
            listener.close()
            proc.kill()
            proc.wait(timeout=5.0)

    def test_py_socket__executes_binary_with_cleanup(self) -> None:
        """Verify execute_binary stages binary or script to temporary file, runs, and unlinks."""

        listener = transport.TcpListener("127.0.0.1", 0)
        port = listener.port

        options = py_socket.PySocketPlugin.extract_options({})
        plugin_config = py_socket.PySocketPlugin.build_config("127.0.0.1", port, options)
        runtime = py_socket.PySocketPlugin.build_runtime(plugin_config)

        proc = self._spawn_launcher(runtime.launcher)
        raw_transport: contract.ITransport | None = None

        try:
            raw_transport = listener.accept(timeout=5.0)
            connection = runtime.create_connection(raw_transport)
            assert isinstance(connection, py_socket.PySocketConnection)
            connection.handshake()

            script_payload = b"#!/bin/sh\necho 'channel_binary_staging_success'\n"
            b64 = util.convert_to_base64(script_payload)
            connection.write(f"execute_binary(store_file(decode_base64({b64!r})), cleanup=True)\n".encode())

            response = b"".join(connection.read())
            assert b"channel_binary_staging_success" in response

            connection.close()
        finally:
            if raw_transport is not None:
                raw_transport.close()
            listener.close()
            proc.kill()
            proc.wait(timeout=5.0)
