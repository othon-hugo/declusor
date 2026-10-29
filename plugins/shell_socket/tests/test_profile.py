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

        renderer = shell_socket.ShellSocketRenderer()
        source_b64 = util.convert_to_base64(b"echo 'hello from shell'")
        rendered = renderer.render_operation_command(config.OperationCode.EXEC_FILE, source_b64)
        assert rendered == f'execute_source "$(decode_b64 {util.quote(source_b64)})"'

    def test_renderer__render_exec_file__binary_payload__renders_binary_execution_with_cleanup(self) -> None:
        """Verify EXEC_FILE opcode with non-UTF8 binary renders execute_binary call with cleanup."""

        renderer = shell_socket.ShellSocketRenderer()
        binary_payload = b"\x7fELF\x02\x01\x01\x00\xff\xfe\xfd\x80"
        binary_b64 = util.convert_to_base64(binary_payload)
        rendered = renderer.render_operation_command(config.OperationCode.EXEC_FILE, binary_b64)
        assert rendered == f'execute_binary --cleanup "$(decode_b64 {util.quote(binary_b64)} | store_file)"'

    def test_renderer__render_store_file__renders_store_file_call_with_destination(self) -> None:
        """Verify STORE_FILE opcode renders store_file call with destination path."""

        renderer = shell_socket.ShellSocketRenderer()
        rendered = renderer.render_operation_command(config.OperationCode.STORE_FILE, "AAAA==", "/tmp/out")
        assert rendered == f"decode_b64 {util.quote('AAAA==')} | store_file {util.quote('/tmp/out')}"

        rendered_no_dest = renderer.render_operation_command(config.OperationCode.STORE_FILE, "AAAA==")
        assert rendered_no_dest == f"decode_b64 {util.quote('AAAA==')} | store_file"

    def test_renderer__render_operation_command__safely_escapes_special_characters(self) -> None:
        """Verify render_operation_command safely quotes arguments containing special characters."""

        renderer = shell_socket.ShellSocketRenderer()
        rendered = renderer.render_operation_command(config.OperationCode.STORE_FILE, "payload", "path with 'quotes' & $vars")
        expected_path = util.quote("path with 'quotes' & $vars")
        assert rendered == f"decode_b64 {util.quote('payload')} | store_file {expected_path}"

    def test_renderer__render_exec_file__with_arguments__appends_quoted_arguments(self) -> None:
        """Verify EXEC_FILE with positional arguments properly escapes and appends arguments."""

        renderer = shell_socket.ShellSocketRenderer()
        source_b64 = util.convert_to_base64(b"echo 'hello'")
        rendered = renderer.render_operation_command(config.OperationCode.EXEC_FILE, source_b64, "first", "second arg with spaces")
        expected = f'execute_source "$(decode_b64 {util.quote(source_b64)})" {util.quote("first")} {util.quote("second arg with spaces")}'
        assert rendered == expected

    def test_renderer__render_exec_file__binary_payload_with_arguments__appends_quoted_arguments(self) -> None:
        """Verify binary EXEC_FILE with positional arguments appends arguments after cleanup flag."""

        renderer = shell_socket.ShellSocketRenderer()
        binary_payload = b"\x7fELF\x00\xff"
        binary_b64 = util.convert_to_base64(binary_payload)
        rendered = renderer.render_operation_command(config.OperationCode.EXEC_FILE, binary_b64, "--opt", "val")
        expected = f'execute_binary --cleanup "$(decode_b64 {util.quote(binary_b64)} | store_file)" {util.quote("--opt")} {util.quote("val")}'
        assert rendered == expected

    def test_renderer__render_payload_execution__without_arguments__returns_none(self) -> None:
        """Verify EXEC_FILE without arguments returns None."""

        renderer = shell_socket.ShellSocketRenderer()
        assert renderer.render_operation_command(config.OperationCode.EXEC_FILE) is None

    def test_renderer__render_payload_execution__invalid_base64__falls_back_to_execute_source(self) -> None:
        """Verify payload execution with invalid base64 string safely falls back to execute_source."""

        renderer = shell_socket.ShellSocketRenderer()
        invalid_b64 = "!!!not_valid_b64!!!"
        rendered = renderer.render_operation_command(config.OperationCode.EXEC_FILE, invalid_b64)
        assert rendered == f'execute_source "$(decode_b64 {util.quote(invalid_b64)})"'

    def test_renderer__render_store_file__without_arguments__returns_none(self) -> None:
        """Verify STORE_FILE without arguments returns None."""

        renderer = shell_socket.ShellSocketRenderer()
        assert renderer.render_operation_command(config.OperationCode.STORE_FILE) is None

    def test_renderer__render_operation_command__unsupported_opcode__returns_none(self) -> None:
        """Verify unsupported opcodes return None."""

        empty_renderer = shell_socket.ShellSocketRenderer(_supported_operations=frozenset())
        assert empty_renderer.supported_operations == frozenset()
        assert empty_renderer.render_operation_command(config.OperationCode.STORE_FILE) is None
        assert empty_renderer.render_operation_command(config.OperationCode.EXEC_COMMAND, "ls") is None

    def test_renderer__render_load_module__renders_shell_source_execution_call(self) -> None:
        """Verify LOAD_MODULE opcode decodes module and renders execute_source call."""

        renderer = shell_socket.ShellSocketRenderer()
        module_b64 = util.convert_to_base64(b"x=42\necho $x")
        rendered = renderer.render_operation_command(config.OperationCode.LOAD_MODULE, module_b64)
        assert rendered == f'execute_source "$(decode_b64 {util.quote(module_b64)})"'

    def test_renderer__render_exec_command__returns_command_unaltered(self) -> None:
        """Verify EXEC_COMMAND returns the command string unaltered."""

        renderer = shell_socket.ShellSocketRenderer()

        cmd = "echo hello && ls -la /tmp"
        assert renderer.render_operation_command(config.OperationCode.EXEC_COMMAND, cmd) == cmd
        assert renderer.render_operation_command(config.OperationCode.EXEC_COMMAND) == ""

    def test_renderer__render_exec_command__trailing_newlines__strips_newlines(self) -> None:
        """Verify EXEC_COMMAND strips trailing CRLF and LF newlines."""

        renderer = shell_socket.ShellSocketRenderer()
        assert renderer.render_operation_command(config.OperationCode.EXEC_COMMAND, "whoami\n") == "whoami"
        assert renderer.render_operation_command(config.OperationCode.EXEC_COMMAND, "id\r\n") == "id"

    def test_renderer__render_exec_code__returns_code_unaltered(self) -> None:
        """Verify EXEC_CODE returns the shell code unaltered."""

        renderer = shell_socket.ShellSocketRenderer()

        code = "VAR='value'; echo $VAR"
        assert renderer.render_operation_command(config.OperationCode.EXEC_CODE, code) == code
        assert renderer.render_operation_command(config.OperationCode.EXEC_CODE) == ""

    def test_renderer__render_exec_code__trailing_newlines__strips_newlines(self) -> None:
        """Verify EXEC_CODE strips trailing CRLF and LF newlines."""

        renderer = shell_socket.ShellSocketRenderer()
        assert renderer.render_operation_command(config.OperationCode.EXEC_CODE, "x=1\n") == "x=1"
        assert renderer.render_operation_command(config.OperationCode.EXEC_CODE, "x=1\r\n") == "x=1"

    def test_renderer__render_operation_command__non_string_arguments__converts_safely(self) -> None:
        """Verify non-string arguments are safely coerced to strings in command rendering."""

        renderer = shell_socket.ShellSocketRenderer()
        source_b64 = util.convert_to_base64(b"echo num")
        rendered = renderer.render_operation_command(config.OperationCode.EXEC_FILE, source_b64, 123, True)
        assert rendered == f'execute_source "$(decode_b64 {util.quote(source_b64)})" {util.quote("123")} {util.quote("True")}'

        rendered_store = renderer.render_operation_command(config.OperationCode.STORE_FILE, "AAAA==", 456)
        assert rendered_store == f"decode_b64 {util.quote('AAAA==')} | store_file {util.quote('456')}"
