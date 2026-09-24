import py_socket
import pytest

from declusor import config


def test_py_socket_profile_render_operation_command_exec_file() -> None:
    """Verify EXEC_FILE opcode renders execute_base64_encoded_value call."""
    profile = py_socket.DEFAULT_PY_SOCKET
    rendered = profile.render_operation_command(config.OperationCode.EXEC_FILE, "AAAA==")
    assert rendered == "execute_base64_encoded_value('AAAA==')"


def test_py_socket_profile_render_operation_command_store_file() -> None:
    """Verify STORE_FILE opcode renders store_base64_encoded_value call with destination path."""
    profile = py_socket.DEFAULT_PY_SOCKET
    rendered = profile.render_operation_command(config.OperationCode.STORE_FILE, "AAAA==", "/tmp/out")
    assert rendered == "store_base64_encoded_value('AAAA==', '/tmp/out')"


def test_py_socket_profile_supported_functions_are_immutable() -> None:
    """Verify supported functions mapping in PySocketProfile cannot be modified."""
    profile = py_socket.PySocketProfile(name="test", ack_server_raw=b"\x00", ack_client_raw=b"\xab" * 32)
    with pytest.raises(TypeError):
        profile._supported_functions[config.OperationCode.EXEC_FILE] = "changed"  # type: ignore[index]
