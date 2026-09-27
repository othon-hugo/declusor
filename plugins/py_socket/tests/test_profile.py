import declusor_py_socket as py_socket
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


def test_py_socket_profile_render_operation_command_with_special_characters() -> None:
    """Verify render_operation_command safely quotes arguments containing quotes and special characters."""

    profile = py_socket.DEFAULT_PY_SOCKET
    rendered = profile.render_operation_command(config.OperationCode.STORE_FILE, "payload", "path with 'quotes' & $vars")
    assert rendered == "store_base64_encoded_value('payload', \"path with 'quotes' & $vars\")"
    assert profile.render_operation_command(config.OperationCode.EXEC_FILE) == "execute_base64_encoded_value()"

    empty_profile = py_socket.PySocketProfile(
        name="empty",
        ack_server_raw=b"\x00",
        ack_client_raw=b"\xab" * 32,
        _supported_functions={},
    )
    assert empty_profile.render_operation_command(config.OperationCode.EXEC_FILE) is None
