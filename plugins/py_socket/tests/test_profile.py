from declusor import config, util

import declusor_py_socket as py_socket


class TestPySocketRenderer:
    """Verify operation command rendering and supported operations in PySocketRenderer."""

    def test_renderer__supported_operations__is_immutable_frozenset(self) -> None:
        """Verify supported operations set in PySocketRenderer contains expected opcodes."""

        renderer = py_socket.PySocketRenderer()
        assert isinstance(renderer.supported_operations, frozenset)
        assert renderer.supported_operations == frozenset(
            {
                config.OperationCode.EXEC_COMMAND,
                config.OperationCode.EXEC_CODE,
                config.OperationCode.EXEC_FILE,
                config.OperationCode.STORE_FILE,
                config.OperationCode.LOAD_MODULE,
            }
        )

    def test_renderer__render_exec_file__renders_python_source_execution_call(self) -> None:
        """Verify EXEC_FILE opcode with Python source renders execute_source call."""

        renderer = py_socket.DEFAULT_PY_SOCKET
        source_b64 = util.convert_to_base64(b"print('hello')")
        rendered = renderer.render_operation_command(config.OperationCode.EXEC_FILE, source_b64)
        assert rendered == f"execute_source(decode_base64({source_b64!r}).decode('utf-8'))"

    def test_renderer__render_exec_file__binary_payload__renders_binary_execution_with_cleanup(self) -> None:
        """Verify EXEC_FILE opcode with non-UTF8 binary renders execute_binary call with cleanup."""

        renderer = py_socket.DEFAULT_PY_SOCKET
        binary_payload = b"\x7fELF\x02\x01\x01\x00\xff\xfe\xfd\x80"
        binary_b64 = util.convert_to_base64(binary_payload)
        rendered = renderer.render_operation_command(config.OperationCode.EXEC_FILE, binary_b64)
        assert rendered == f"execute_binary(store_file(decode_base64({binary_b64!r})), cleanup=True)"

    def test_renderer__render_store_file__renders_store_file_call_with_destination(self) -> None:
        """Verify STORE_FILE opcode renders store_file call with destination path."""

        renderer = py_socket.DEFAULT_PY_SOCKET
        rendered = renderer.render_operation_command(config.OperationCode.STORE_FILE, "AAAA==", "/tmp/out")
        assert rendered == "store_file(decode_base64('AAAA=='), '/tmp/out')"

        rendered_no_dest = renderer.render_operation_command(config.OperationCode.STORE_FILE, "AAAA==")
        assert rendered_no_dest == "store_file(decode_base64('AAAA=='))"

    def test_renderer__render_operation_command__safely_escapes_special_characters(self) -> None:
        """Verify render_operation_command safely quotes arguments containing quotes and special characters."""

        renderer = py_socket.DEFAULT_PY_SOCKET
        rendered = renderer.render_operation_command(config.OperationCode.STORE_FILE, "payload", "path with 'quotes' & $vars")
        assert rendered == "store_file(decode_base64('payload'), \"path with 'quotes' & $vars\")"
        assert renderer.render_operation_command(config.OperationCode.EXEC_FILE) is None

        empty_renderer = py_socket.PySocketRenderer(_supported_operations=frozenset())
        assert empty_renderer.render_operation_command(config.OperationCode.STORE_FILE) is None

    def test_renderer__render_load_module__renders_python_source_execution_call(self) -> None:
        """Verify LOAD_MODULE opcode decodes module and renders execute_source call."""

        renderer = py_socket.DEFAULT_PY_SOCKET
        module_b64 = util.convert_to_base64(b"x = 42\nprint(x)")
        rendered = renderer.render_operation_command(config.OperationCode.LOAD_MODULE, module_b64)
        assert rendered == f"execute_source(decode_base64({module_b64!r}).decode('utf-8'))"

    def test_renderer__render_exec_code__wraps_in_execute_source(self) -> None:
        """Verify EXEC_CODE opcode wraps code in execute_source call."""

        renderer = py_socket.DEFAULT_PY_SOCKET

        py_code = "import os\nprint(os.getpid())"
        assert renderer.render_operation_command(config.OperationCode.EXEC_CODE, py_code) == f"execute_source({py_code!r})"

        py_shebang = "#!/usr/bin/env python\nprint('hello')"
        assert renderer.render_operation_command(config.OperationCode.EXEC_CODE, py_shebang) == f"execute_source({py_shebang!r})"

        assert renderer.render_operation_command(config.OperationCode.EXEC_CODE) == "execute_source('')"

    def test_renderer__render_exec_command__wraps_command_in_execute_system_command(self) -> None:
        """Verify EXEC_COMMAND deterministically wraps commands in execute_system_command."""

        renderer = py_socket.DEFAULT_PY_SOCKET

        cmd = "uname -a && whoami"
        expected = "execute_system_command('uname -a && whoami')"
        assert renderer.render_operation_command(config.OperationCode.EXEC_COMMAND, cmd) == expected

        cmd_quotes = "echo 'hello world' \"nested\""
        expected_quotes = f"execute_system_command({util.quote(cmd_quotes)})"
        assert renderer.render_operation_command(config.OperationCode.EXEC_COMMAND, cmd_quotes) == expected_quotes

    def test_renderer__render_exec_command_empty__returns_empty_execute_system_command_call(self) -> None:
        """Verify EXEC_COMMAND with empty or missing arguments returns empty execute_system_command call."""

        renderer = py_socket.DEFAULT_PY_SOCKET

        assert renderer.render_operation_command(config.OperationCode.EXEC_COMMAND) == "execute_system_command('')"
        assert renderer.render_operation_command(config.OperationCode.EXEC_COMMAND, "") == "execute_system_command('')"
