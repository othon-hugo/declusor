import pytest
import shell_socket

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
