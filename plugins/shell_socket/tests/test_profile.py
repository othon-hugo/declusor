import declusor_shell_socket as shell_socket
import pytest

from declusor import config


def test_profile_supported_functions_are_immutable() -> None:
    """Verify supported functions mapping in shell_socket.ShellSocketProfile cannot be modified."""

    profile = shell_socket.ShellSocketProfile(name="test", ack_server_raw=b"\x00", ack_client_raw=b"ack")

    with pytest.raises(TypeError):
        profile._supported_functions[config.OperationCode.EXEC_FILE] = "changed"  # type: ignore[index]


def test_profile_render_operation_command() -> None:
    """Verify render_operation_command produces correct shell function invocations."""

    profile = shell_socket.DEFAULT_SHELL_SOCKET
    rendered_exec = profile.render_operation_command(config.OperationCode.EXEC_FILE, "payload==")
    assert rendered_exec is not None
    assert "execute_base64_encoded_value payload==" in rendered_exec

    rendered_store = profile.render_operation_command(config.OperationCode.STORE_FILE, "payload==", "/tmp/f")
    assert rendered_store is not None
    assert "store_base64_encoded_value payload== /tmp/f" in rendered_store

    rendered_spaces = profile.render_operation_command(config.OperationCode.STORE_FILE, "payload==", "path with spaces/file.sh")
    assert rendered_spaces == "store_base64_encoded_value payload== 'path with spaces/file.sh'"

    empty_profile = shell_socket.ShellSocketProfile(name="empty", ack_server_raw=b"\x00", ack_client_raw=b"ack", _supported_functions={})
    assert empty_profile.render_operation_command(config.OperationCode.STORE_FILE) is None


def test_profile_render_operation_command_exec_command() -> None:
    """Verify EXEC_COMMAND returns the command string unaltered."""

    profile = shell_socket.DEFAULT_SHELL_SOCKET

    cmd = "echo hello && ls -la /tmp"
    assert profile.render_operation_command(config.OperationCode.EXEC_COMMAND, cmd) == cmd
    assert profile.render_operation_command(config.OperationCode.EXEC_COMMAND) == ""


def test_profile_render_operation_command_exec_code() -> None:
    """Verify EXEC_CODE returns the shell code unaltered."""

    profile = shell_socket.DEFAULT_SHELL_SOCKET

    code = "VAR='value'; echo $VAR"
    assert profile.render_operation_command(config.OperationCode.EXEC_CODE, code) == code
    assert profile.render_operation_command(config.OperationCode.EXEC_CODE) == ""


def test_profile_render_operation_command_load_module() -> None:
    """Verify LOAD_MODULE renders execute_base64_encoded_value with base64 payload."""

    profile = shell_socket.DEFAULT_SHELL_SOCKET

    rendered = profile.render_operation_command(config.OperationCode.LOAD_MODULE, "mod_payload==")
    assert rendered == "execute_base64_encoded_value mod_payload=="
