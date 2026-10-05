import declusor_shell_socket as shell_socket

from declusor import config, util


class TestShellSocketRenderer:
    """Verify operation command rendering and supported operations in ShellSocketRenderer."""

    def test_renderer__supported_operations__is_immutable_frozenset(self) -> None:
        """Verify supported operations set in ShellSocketRenderer contains expected opcodes."""

        renderer = shell_socket.ShellSocketRenderer()
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

    def test_renderer__render_exec_file__renders_shell_source_execution_call(self) -> None:
        """Verify EXEC_FILE opcode with shell script renders execute_source call."""

        renderer = shell_socket.DEFAULT_SHELL_SOCKET
        source_b64 = util.convert_to_base64(b"echo 'hello from shell'")
        rendered = renderer.render_operation_command(config.OperationCode.EXEC_FILE, source_b64)
        assert rendered == f'execute_source "$(decode_b64 {util.quote(source_b64)})"'

    def test_renderer__render_exec_file__binary_payload__renders_binary_execution_with_cleanup(self) -> None:
        """Verify EXEC_FILE opcode with non-UTF8 binary renders execute_binary call with cleanup."""

        renderer = shell_socket.DEFAULT_SHELL_SOCKET
        binary_payload = b"\x7fELF\x02\x01\x01\x00\xff\xfe\xfd\x80"
        binary_b64 = util.convert_to_base64(binary_payload)
        rendered = renderer.render_operation_command(config.OperationCode.EXEC_FILE, binary_b64)
        assert rendered == f'execute_binary --cleanup "$(decode_b64 {util.quote(binary_b64)} | store_file)"'

    def test_renderer__render_store_file__renders_store_file_call_with_destination(self) -> None:
        """Verify STORE_FILE opcode renders store_file call with destination path."""

        renderer = shell_socket.DEFAULT_SHELL_SOCKET
        rendered = renderer.render_operation_command(config.OperationCode.STORE_FILE, "AAAA==", "/tmp/out")
        assert rendered == f"decode_b64 {util.quote('AAAA==')} | store_file {util.quote('/tmp/out')}"

        rendered_no_dest = renderer.render_operation_command(config.OperationCode.STORE_FILE, "AAAA==")
        assert rendered_no_dest == f"decode_b64 {util.quote('AAAA==')} | store_file"

    def test_renderer__render_operation_command__safely_escapes_special_characters(self) -> None:
        """Verify render_operation_command safely quotes arguments containing special characters."""

        renderer = shell_socket.DEFAULT_SHELL_SOCKET
        rendered = renderer.render_operation_command(config.OperationCode.STORE_FILE, "payload", "path with 'quotes' & $vars")
        expected_path = util.quote("path with 'quotes' & $vars")
        assert rendered == f"decode_b64 {util.quote('payload')} | store_file {expected_path}"
        assert renderer.render_operation_command(config.OperationCode.EXEC_FILE) is None

        empty_renderer = shell_socket.ShellSocketRenderer(_supported_operations=frozenset())
        assert empty_renderer.render_operation_command(config.OperationCode.STORE_FILE) is None

    def test_renderer__render_load_module__renders_shell_source_execution_call(self) -> None:
        """Verify LOAD_MODULE opcode decodes module and renders execute_source call."""

        renderer = shell_socket.DEFAULT_SHELL_SOCKET
        module_b64 = util.convert_to_base64(b"x=42\necho $x")
        rendered = renderer.render_operation_command(config.OperationCode.LOAD_MODULE, module_b64)
        assert rendered == f'execute_source "$(decode_b64 {util.quote(module_b64)})"'

    def test_renderer__render_exec_command__returns_command_unaltered(self) -> None:
        """Verify EXEC_COMMAND returns the command string unaltered."""

        renderer = shell_socket.DEFAULT_SHELL_SOCKET

        cmd = "echo hello && ls -la /tmp"
        assert renderer.render_operation_command(config.OperationCode.EXEC_COMMAND, cmd) == cmd
        assert renderer.render_operation_command(config.OperationCode.EXEC_COMMAND) == ""

    def test_renderer__render_exec_code__returns_code_unaltered(self) -> None:
        """Verify EXEC_CODE returns the shell code unaltered."""

        renderer = shell_socket.DEFAULT_SHELL_SOCKET

        code = "VAR='value'; echo $VAR"
        assert renderer.render_operation_command(config.OperationCode.EXEC_CODE, code) == code
        assert renderer.render_operation_command(config.OperationCode.EXEC_CODE) == ""
